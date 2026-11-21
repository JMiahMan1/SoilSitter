"""
SoilSitter case: a battery ESPHome soil-moisture sensor that hangs over the pot
rim and hides behind the pot, instead of standing up in the soil.

Three printed parts:

  body       bay (outside the pot) + over-rim hook + inside leg + probe sleeve
  bay_lid    closes the pot side of the bay (2 M2.5 screws + a bottom lip)
  probe_cap  seals the probe sleeve (trapped top and bottom, silicone gasket)

Coordinates (mm):

  +Z  up, Z=0 is the top of the pot rim
  +Y  away from the pot.  Pot outer wall = Y 0, pot inner wall = Y -RIM_GAP
  +X  along the pot's rim (the hook is symmetric about X=0)

The bay hangs at Y > 0 (behind the pot), the leg runs down the inside of the
rim, and the probe sleeve (Y < -14) sits in the soil against the pot wall.

    .venv-cad/bin/python cad/soilsitter.py                 # rim 9 mm (default)
    .venv-cad/bin/python cad/soilsitter.py --rim-gap 6
    .venv-cad/bin/python cad/soilsitter.py --rim-gap 12
    .venv-cad/bin/python cad/check_fit.py                  # parts vs real hardware
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build123d import (Axis, Box, Cylinder, Plane, Polygon, Pos, Rot, chamfer,
                       export_stl, extrude, fillet)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STL = ROOT / "stl"

# ---------------------------------------------------------------------------
# Bay and hook
# ---------------------------------------------------------------------------
BAY_W = 88.0          # outside width, X
BAY_D = 30.0          # outside depth, Y (0..30, away from the pot)
BAY_H = 62.0          # outside height, Z
BAY_TOP = 4.5         # bridge / top wall thickness above Z=0
BAY_BOT = BAY_TOP - BAY_H          # -53.5
WALL_SIDE = 3.0
WALL_OUT = 3.0
WALL_BOT = 4.5
TOP_WALL = 4.5
CORNER_R = 10.0

BAY_FRONT = 2.5       # bay stands this far off the pot's outer wall
RIM_GAP = 9.0         # pot rim thickness the hook is cut for (parameter)
LEG_T = 3.5           # leg thickness, Y
LEG_W = 12.0          # leg width, X
BRIDGE_W = 64.0       # hook bridge width, X
BRIDGE_OVERHANG = 2.0 # bridge reach past the leg on the pot side

# ---------------------------------------------------------------------------
# Probe sleeve (inside the pot) - holds a 98 x 23 x 4 mm capacitive sensor
# ---------------------------------------------------------------------------
PROBE_W = 32.0
PROBE_D = 13.0
PROBE_Y_BACK = -11.5               # face nearest the pot wall
PROBE_Y_FRONT = PROBE_Y_BACK - PROBE_D
PROBE_TOP = -8.0                   # just below the rim
PROBE_BOT = -140.0
PROBE_WALL_FRONT = 1.6             # sensing face (reads through this)
PROBE_WALL_SIDE = 3.5
PROBE_CAP_T = 2.5

CAV_X = PROBE_W / 2 - PROBE_WALL_SIDE          # 12.5 -> 25 mm cavity
CAV_Y_BACK = PROBE_Y_BACK - PROBE_CAP_T        # -14.0
CAV_Y_FRONT = PROBE_Y_FRONT + PROBE_WALL_FRONT # -20.9
CAV_Z_TOP = -30.0                              # collar underside
CAV_Z_BOT = -136.0

# Wire route: cavity -> pocket -> groove up the leg -> tunnel over the rim
# -> notch down into the bay.
WIRE_W = 5.0
WIRE_D = 2.2
WIRE_TOP_Z = 1.0
TUNNEL_Z0, TUNNEL_Z1 = 1.0, 3.2
NOTCH_Y0, NOTCH_Y1 = 3.0, 7.0

# Fasteners: self-tapping into printed pilots, no heat-set inserts
LID_SCREW_PILOT = 2.1              # M2.5
BOSS_X = 37.0
LID_TOP_SCREW_Z = 2.25
LID_BOT_SCREW_Z = -41.0
BOSS_Y = 7.0

# Charging: M16 USB-C panel pigtail through the outer wall
CHARGE_PORT_X = -30.0
CHARGE_PORT_Z = -40.0
CHARGE_PORT_D = 16.2


def box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float):
    """Axis-aligned box from two opposite corners."""
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(
        x1 - x0, y1 - y0, z1 - z0
    )


def cyl_y(x: float, z: float, y0: float, y1: float, d: float):
    """Cylinder along Y: lid screw pilots and their clearance holes."""
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(d / 2, abs(y1 - y0))


def near(part, coord: str, value: float, tol: float = 0.02):
    """Edges whose centre sits at `value` on one coordinate (X, Y or Z)."""
    return [e for e in part.edges()
            if abs(getattr(e.center(), coord) - value) < tol]


# ---------------------------------------------------------------------------
# Body
# ---------------------------------------------------------------------------
def make_body(rim_gap: float = RIM_GAP):
    leg_y_out = -rim_gap                  # against the pot's inner wall
    leg_y_in = leg_y_out - LEG_T
    bridge_y0 = leg_y_in - BRIDGE_OVERHANG

    # Bay shell: solid block with rounded outer corners, then hollowed from the
    # pot side (Y = 0) so the lid is a flat plate with a flat gasket face.
    body = box(-BAY_W / 2, BAY_W / 2, BAY_FRONT, BAY_FRONT + BAY_D,
                BAY_BOT, BAY_TOP)
    outer_verticals = [e for e in body.edges().filter_by(Axis.Z)
                       if e.center().Y > BAY_FRONT + BAY_D / 2]
    body = fillet(outer_verticals, CORNER_R)
    body = chamfer(near(body, "Z", BAY_BOT), 1.2)

    cav_x = BAY_W / 2 - WALL_SIDE         # 41.0
    cav_y1 = BAY_FRONT + BAY_D - WALL_OUT  # 29.5
    cav_z1 = BAY_TOP - TOP_WALL           # 0.0
    cav_z0 = BAY_BOT + WALL_BOT           # -50.3
    body -= box(-cav_x, cav_x, BAY_FRONT - 1, cav_y1, cav_z0, cav_z1)

    # Hook bridge over the rim, leg down the pot's inner wall.
    body += box(-BRIDGE_W / 2, BRIDGE_W / 2, bridge_y0, BAY_FRONT,
                0, BAY_TOP)
    body += box(-LEG_W / 2, LEG_W / 2, leg_y_in, leg_y_out, CAV_Z_TOP, BAY_TOP)

    # Probe sleeve, fused to the leg; the top 22 mm is a solid collar.
    body += box(-PROBE_W / 2, PROBE_W / 2, PROBE_Y_FRONT, PROBE_Y_BACK,
                PROBE_BOT, PROBE_TOP)
    # Neck between the sleeve's back face and the leg. At a 9 mm rim the two
    # boxes already overlap by 1 mm, but a 6 mm rim pulls the leg out to Y=-9.5
    # and the sleeve would float free, so bridge the gap explicitly.
    body += box(-PROBE_W / 2, PROBE_W / 2, PROBE_Y_BACK, leg_y_out,
                CAV_Z_TOP, PROBE_TOP)

    # 45-degree roof over the sleeve's top. The sleeve's flat top is the one
    # surface that hangs in mid-air when the body is printed bay-down, and a flat
    # 25 x 6 mm ceiling there needs support. A ridge costs nothing: it is inside
    # the pot, below the rim, out of sight, and it stiffens the sleeve/leg joint.
    apex_z = PROBE_TOP + (PROBE_Y_BACK - PROBE_Y_FRONT) / 2
    roof = Plane.YZ * Polygon((PROBE_Y_FRONT, PROBE_TOP),
                              ((PROBE_Y_FRONT + PROBE_Y_BACK) / 2, apex_z),
                              (PROBE_Y_BACK, PROBE_TOP), align=None)
    body += extrude(roof, amount=PROBE_W / 2, both=True)

    # Cavity the sensor slides into, plus the cap seat behind it.
    body -= box(-CAV_X, CAV_X, CAV_Y_FRONT, CAV_Y_BACK, CAV_Z_BOT, CAV_Z_TOP)
    body -= box(-CAV_X + 0.1, CAV_X - 0.1, CAV_Y_BACK, PROBE_Y_BACK + 0.15,
                CAV_Z_BOT, CAV_Z_TOP)

    # Tip lip traps the bottom of the cap; the collar traps its top.
    body += box(-PROBE_W / 2, PROBE_W / 2, CAV_Y_BACK, PROBE_Y_BACK,
                CAV_Z_BOT - 1.5, CAV_Z_BOT - 0.5)

    # Wire route: pocket (opens into the cavity) -> groove up the leg
    # -> tunnel over the rim -> notch down into the bay.
    # The groove starts at the cavity's back face, or at the leg's inner face
    # when the leg is pulled further out by a thick rim - otherwise a 12 mm rim
    # leaves a 0.7 mm slot that no wire fits through.
    wire_y0 = min(CAV_Y_BACK, leg_y_in)
    body -= box(-WIRE_W / 2, WIRE_W / 2, wire_y0, leg_y_in + WIRE_D,
                CAV_Z_TOP, WIRE_TOP_Z)
    body -= box(-WIRE_W / 2, WIRE_W / 2, wire_y0, NOTCH_Y1,
                TUNNEL_Z0, TUNNEL_Z1)
    body -= box(-WIRE_W / 2, WIRE_W / 2, NOTCH_Y0, NOTCH_Y1, 0.0, TUNNEL_Z0)

    # Entry chamfer at the probe's tip, and a soft edge on the sensing face.
    body = chamfer(near(body, "Z", PROBE_BOT), 2.0)

    # Charging port: M16 panel-mount USB-C pigtail in the outer wall, low and
    # behind the pot (recessed O-ring seat on the outside).
    body -= cyl_y(CHARGE_PORT_X, CHARGE_PORT_Z,
                  BAY_FRONT + BAY_D - WALL_OUT - 1, BAY_FRONT + BAY_D + 1,
                  CHARGE_PORT_D)
    body -= cyl_y(CHARGE_PORT_X, CHARGE_PORT_Z,
                  BAY_FRONT + BAY_D - 1.2, BAY_FRONT + BAY_D + 1,
                  CHARGE_PORT_D + 3.4)

    # Lid screws: two into the top wall, two into corner bosses.
    for sx in (-BOSS_X, BOSS_X):
        body += box(sx - 5.0, sx + 5.0, BAY_FRONT, BAY_FRONT + BOSS_Y,
                     -45.0, -37.0)
        body -= cyl_y(sx, LID_TOP_SCREW_Z, -1.0, 12.0, LID_SCREW_PILOT)
        body -= cyl_y(sx, LID_BOT_SCREW_Z, -1.0, BAY_FRONT + BOSS_Y,
                      LID_SCREW_PILOT)

    return body



# ---------------------------------------------------------------------------
# Bay lid, probe cap, gasket templates
# ---------------------------------------------------------------------------
def make_bay_lid():
    t = 2.5
    lid = box(-BAY_W / 2 + 0.15, BAY_W / 2 - 0.15, 0, BAY_FRONT,
              BAY_BOT + 0.15, BAY_TOP - 0.15)
    # The hook bridge owns the bay's top strip in the middle; notch the lid
    # around it and seal that corner with silicone on assembly.
    lid -= box(-BRIDGE_W / 2 - 0.2, BRIDGE_W / 2 + 0.2, -1, BAY_FRONT + 0.3,
               -0.2, BAY_TOP + 1)
    lid = chamfer(lid.edges().filter_by(Axis.Y), 1.2)
    for sx in (-BOSS_X, BOSS_X):
        for sz in (LID_TOP_SCREW_Z, LID_BOT_SCREW_Z):
            lid -= cyl_y(sx, sz, -1.0, BAY_FRONT + 1, 2.7)     # screw clearance
            lid -= cyl_y(sx, sz, -0.01, 1.6, 4.6)              # counterbore
    return lid


def make_probe_cap():
    cap = box(-CAV_X + 0.1, CAV_X - 0.1, CAV_Y_BACK, PROBE_Y_BACK,
              CAV_Z_BOT - 0.5, CAV_Z_TOP)
    cap = chamfer(cap.edges().filter_by(Axis.X), 1.0)
    # Shallow ribs make it a light press fit while the silicone cures.
    for sx in (-1, 1):
        cap += box(sx * (CAV_X - 0.4), sx * (CAV_X + 0.15),
                   -13.0, -12.0, CAV_Z_BOT + 6, CAV_Z_TOP - 6)
    return cap


def make_bay_gasket():
    """1 mm silicone sheet gasket (or print in TPU at 100 % infill).

    It lies on the lid's inner face (Y = 0), inside the bay's 1 mm rebate, and is
    compressed against the bay's shoulder when the screws pull the lid home. The
    hook bridge owns the bay's top strip, so the gasket is notched around it just
    like the lid.
    """
    g = box(-BAY_W / 2 + 2.0, BAY_W / 2 - 2.0, 0.0, 1.0,
            BAY_BOT + 2.0, BAY_TOP - 2.0)
    g -= box(-BAY_W / 2 + 5.0, BAY_W / 2 - 5.0, -1.0, 2.0,
             BAY_BOT + 5.0, BAY_TOP - 5.0)
    g -= box(-BRIDGE_W / 2 - 0.2, BRIDGE_W / 2 + 0.2, -1.0, 2.0,
             -0.2, BAY_TOP + 1)
    return g


def make_probe_gasket():
    """Liner for the cap's seat: it fills the cavity's mouth behind the cap.

    The cap is a plug, not a flanged lid, so this is radial compression in the
    seat rather than a face seal - splash-proof, not submersible.
    """
    g = box(-CAV_X + 0.05, CAV_X - 0.05, CAV_Y_BACK - 1.0, CAV_Y_BACK,
            CAV_Z_BOT + 0.5, CAV_Z_TOP - 0.5)
    g -= box(-CAV_X + 3.0, CAV_X - 3.0, CAV_Y_BACK - 2.0, CAV_Y_BACK + 1.0,
             CAV_Z_BOT + 3.0, CAV_Z_TOP - 3.0)
    return g


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="SoilSitter printable case")
    ap.add_argument("--rim-gap", type=float, default=RIM_GAP,
                    help="pot rim thickness the hook is cut for (mm)")
    ap.add_argument("--suffix", default="",
                    help="file tag, replacing the default rim<gap> "
                         "(e.g. --suffix v2 -> body_v2.stl)")
    ap.add_argument("--no-stl", action="store_true")
    args = ap.parse_args()

    sfx = args.suffix or f"rim{args.rim_gap:g}"
    STL.mkdir(parents=True, exist_ok=True)

    parts = {
        "body": make_body(args.rim_gap),
        "bay_lid": make_bay_lid(),
        "probe_cap": make_probe_cap(),
        "bay_gasket": make_bay_gasket(),
        "probe_gasket": make_probe_gasket(),
    }

    stats = {}
    for name, part in parts.items():
        bb = part.bounding_box()
        stats[name] = {
            "file": f"{name}_{sfx}.stl",
            "volume_cm3": round(part.volume / 1000, 2),
            "bbox_mm": [round(bb.size.X, 2), round(bb.size.Y, 2),
                        round(bb.size.Z, 2)],
            "solids": len(part.solids()),
        }
        if not args.no_stl:
            export_stl(part, str(STL / f"{name}_{sfx}.stl"),
                       tolerance=0.05, angular_tolerance=0.2)
        print(f"{name:14s} {part.volume / 1000:7.2f} cm3  "
              f"{bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:6.1f} mm  "
              f"{len(part.solids())} solid(s)")

    if not args.no_stl:
        (STL / f"manifest_{sfx}.json").write_text(json.dumps(stats, indent=2) + "\n")
        print(f"\nwrote {len(parts)} STLs to {STL} (rim gap {args.rim_gap:g} mm)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

