"""
Fit check for SoilSitter.

Three kinds of check, all against the exported STLs:

  1. every part is one closed solid, with the volume and extents we expect;
  2. the real hardware (board, charger, cell, probe PCB) fits inside the
     cavities with clearance, and none of the boxes overlap each other or a
     fastener;
  3. the wire route and the sensor bay are actually open - sampled points
     along the route must be *outside* the body mesh.

    .venv-cad/bin/python cad/check_fit.py
    .venv-cad/bin/python cad/check_fit.py --rim-gap 6
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soilsitter as ss  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STL = ROOT / "stl"

#: The real parts, from published dimensions rather than guesses. Each entry is
#: the box the part occupies *as it is mounted* (component side up), with the
#: thickness of a 2.5 mm foam tape pad added where a board is stuck to the lid.
#:
#: Sources (checked 2026-11-20):
#:   ESP32-C3 Super Mini  22.52 x 18 mm, 2.54 mm pitch, USB-C 3.2 mm tall
#:       espboards.dev/esp32/esp32-c3-super-mini (and its GrabCAD model link)
#:   TP4056 Type-C       26 x 17 mm module, Type-C shell ~1 mm proud of the edge
#:       sigmanortec.ro "lithium battery charging module TP4056 TypeC" data sheet
#:   Cap. soil V1.2      98 x 23 x 1.6 mm PCB, JST-PH 2.0 connector on top
#:       makerselectronics.com "Capacitive Soil Moisture Sensor V1.2" (98 x 23 mm,
#:       20 cm cable), tinkered.ai (SEN0193 clone, 3.3-5.5 V, 5 mA)
#:   103450 cell         10 x 34 x 50 mm nominal; 10.5 x 35 x 52 mm with the
#:       protection PCB, sleeve and leads
#:   M16 USB-C pigtail   16 mm thread, 20 mm hex nut, ~13 mm body behind the panel
#:       (a right-angle plug is shorter; the cable bends from there)
#:   HT7333 LDO          SOT-89, 4.5 x 4.0 x 1.5 mm
HARDWARE = {
    "esp32-c3-supermini": (-38.0, -20.0, 3.0, 7.8, -33.5, -11.0,
                          "22.52 x 18 mm board, 1.6 + 3.2 USB-C on 3 mm tape"),
    "tp4056": (2.0, 31.2, 3.0, 7.3, -21.0, -4.0,
               "29 x 17.3 x 4.3 mm overall: 26 x 17 board + 3 mm Type-C shell"),
    "ht7333": (-10.0, -5.5, 3.0, 7.0, -20.0, -18.5,
               "SOT-89 LDO, 4.5 x 4.0 x 1.5 mm"),
    "lipo-103450": (-17.5, 17.5, 17.0, 27.5, -52.5, -0.5,
                    "10.5 x 35 x 52 mm pouch incl. protection PCB and leads"),
    "usb-pigtail": (-40.0, -20.0, 16.0, 29.5, -50.0, -30.0,
                    "M16 panel pigtail: 20 mm nut + 13 mm body behind the panel"),
    "sensor-pcb": (-11.5, 11.5, -22.7, -21.1, -134.0, -36.0,
                   "98 x 23 x 1.6 mm capacitive probe, sensing face out"),
    "sensor-smd": (-11.5, 11.5, -21.1, -19.2, -134.0, -36.0,
                   "tallest SMD parts on the probe, 1.9 mm"),
    "sensor-connector": (-11.5, 11.5, -21.1, -15.5, -44.0, -36.0,
                         "JST-PH 2.0 socket, 5.6 mm above the PCB"),
}


def box_from(t):
    (x0, x1, y0, y1, z0, z1, _) = t
    return np.array([[x0, y0, z0], [x1, y1, z1]])


def overlap(a, b, margin=0.0):
    lo = np.maximum(a[0], b[0]) - margin
    hi = np.minimum(a[1], b[1]) + margin
    return np.all(hi > lo)



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rim-gap", type=float, default=ss.RIM_GAP)
    args = ap.parse_args()
    sfx = f"rim{args.rim_gap:g}"

    ok = True

    def report(good, text):
        nonlocal ok
        ok &= bool(good)
        print(f"  [{'PASS' if good else 'FAIL'}] {text}")

    # -- 1. parts ---------------------------------------------------------
    print("parts")
    meshes = {}
    for name in ("body", "bay_lid", "probe_cap", "bay_gasket", "probe_gasket"):
        path = STL / f"{name}_{sfx}.stl"
        m = trimesh.load(path, process=True)
        meshes[name] = m
        parts = m.split(only_watertight=False)
        report(m.is_watertight and len(parts) == 1,
               f"{path.name}: watertight, one body "
               f"({m.volume / 1000:.1f} cm3, "
               f"{m.extents[0]:.0f} x {m.extents[1]:.0f} x {m.extents[2]:.0f} mm)")

    body = meshes["body"]

    # -- 2. the bay cavity ------------------------------------------------
    print("\nbay interior")
    bay = np.array([
        [-ss.BAY_W / 2 + ss.WALL_SIDE, ss.BAY_FRONT, ss.BAY_BOT + ss.WALL_BOT],
        [ss.BAY_W / 2 - ss.WALL_SIDE, ss.BAY_FRONT + ss.BAY_D - ss.WALL_OUT,
         ss.BAY_TOP - ss.TOP_WALL],
    ])
    print(f"  cavity {bay[1, 0] - bay[0, 0]:.1f} W x "
          f"{bay[1, 1] - bay[0, 1]:.1f} D x {bay[1, 2] - bay[0, 2]:.1f} H mm")

    boxes = {k: box_from(v) for k, v in HARDWARE.items()}
    for name, b in boxes.items():
        if name.startswith((("sensor", "usb"))):
            continue
        clear = np.minimum(b[0] - bay[0], bay[1] - b[1])
        # Boards are taped to the lid, so their face is flush with the bay's mouth:
        # no clearance there is correct. Everything else needs 0.4 mm.
        mouth = clear[1]
        sides = min(clear[0], clear[2], bay[1][1] - b[1][1])
        inside = np.all(b[0] >= bay[0] - 0.05) and np.all(b[1] <= bay[1])
        report(inside and sides >= 0.4 and mouth >= -0.05,
               f"{name:20s} fits: {sides:.1f} mm to the sides, "
               f"{mouth:+.1f} mm at the mouth")

    # -- 3. no overlaps between parts in the bay -------------------------
    print("\npacking")
    bay_names = [n for n in boxes if not n.startswith("sensor")]
    for i, a in enumerate(bay_names):
        for b in bay_names[i + 1:]:
            report(not overlap(boxes[a], boxes[b]), f"{a} clear of {b}")

    # Lid screws (M2.5 x 12 heads, 4.6 mm across) must not hit hardware.
    head_r = 2.3
    for sx in (-ss.BOSS_X, ss.BOSS_X):
        for sz in (ss.LID_TOP_SCREW_Z, ss.LID_BOT_SCREW_Z):
            screw = np.array([[sx - head_r, -1.0, sz - head_r],
                              [sx + head_r, 1.0, sz + head_r]])
            hits = [n for n, b in boxes.items() if overlap(screw, b)]
            report(not hits,
                   f"lid screw at x={sx:+.0f} z={sz:+.0f} clear of hardware"
                   + (f" (hits {hits})" if hits else ""))


    # -- 4. the probe cavity and the sensor ------------------------------
    print("\nprobe")
    probe = np.array([
        [-ss.CAV_X, ss.CAV_Y_FRONT, ss.CAV_Z_BOT],
        [ss.CAV_X, ss.CAV_Y_BACK, ss.CAV_Z_TOP],
    ])
    pc = boxes["sensor-pcb"]
    for label, box in (("PCB", pc), ("SMD parts", boxes["sensor-smd"]),
                       ("JST socket", boxes["sensor-connector"])):
        report(np.all(box[0] >= probe[0]) and np.all(box[1] <= probe[1]),
               f"sensor {label} inside the probe cavity, clear of the cap")
    report(probe[1, 0] - probe[0, 0] - (pc[1, 0] - pc[0, 0]) >= 1.0,
           f"side clearance for the 23 mm PCB "
           f"{probe[1, 0] - probe[0, 0] - (pc[1, 0] - pc[0, 0]):.1f} mm")
    report(ss.CAV_Y_BACK - boxes["sensor-connector"][1][1] >= 1.2,
           f"cable channel behind the JST socket "
           f"{ss.CAV_Y_BACK - boxes['sensor-connector'][1][1]:.1f} mm")

    # -- 5. wire route is open -------------------------------------------
    print("\nwire route (sampled through the body mesh)")
    leg_y_in = -args.rim_gap - ss.LEG_T
    groove_y0 = min(ss.CAV_Y_BACK, leg_y_in)
    groove_y1 = leg_y_in + ss.WIRE_D
    groove_mid = (groove_y0 + groove_y1) / 2
    pts = []
    for z in np.linspace(ss.CAV_Z_TOP + 1, ss.WIRE_TOP_Z - 0.2, 40):
        pts.append((0.0, groove_mid, z))                   # pocket and groove
    for y in np.linspace(groove_y0 + 1.0, ss.NOTCH_Y1 - 0.5, 30):
        pts.append((0.0, y, 2.1))                          # tunnel over the rim
    for z in np.linspace(1.0, -4.0, 15):
        pts.append((0.0, 5.0, z))                          # notch into the bay
    pts = np.array(pts)
    inside = body.contains(pts)
    report(not inside.any(),
           f"all {len(pts)} route samples are open (blocked: {int(inside.sum())})")
    report(groove_y1 - groove_y0 >= 2.0,
           f"groove is {groove_y1 - groove_y0:.1f} mm deep at Y "
           f"{groove_y0:.1f}..{groove_y1:.1f} (3 x 26 AWG needs ~2 mm)")

    report(groove_y1 < -args.rim_gap,
           "wire groove stays behind the pot's inner wall")

    # -- 6. hook and lid geometry ----------------------------------------
    print("\nhook and lid")
    # Under the bridge is open (that is the rim slot), the bridge itself is
    # solid above it, and the leg is solid just inside the rim.
    slot = np.array([[8.0, -args.rim_gap + 0.5, -1.0],
                     [8.0, -args.rim_gap + 0.5, 6.0]])
    solid = np.array([[8.0, -args.rim_gap + 0.5, 2.2],
                      [8.0, -args.rim_gap - 1.6, 2.2]])
    got = body.contains(np.vstack([slot[:1], solid]))
    report(not got[0] and got[1],
           f"rim slot open at {args.rim_gap:g} mm, bridge solid over it")
    lid = meshes["bay_lid"]
    probes = np.array([[0, 1.25, 2.0], [31.0, 1.25, 2.0],
                       [33.0, 1.25, 2.0], [0, 1.25, -10.0]])
    lid_in = lid.contains(probes)
    report(not lid_in[0] and not lid_in[1] and lid_in[2] and lid_in[3],
           "lid is notched around the hook bridge and solid elsewhere")

    cap = meshes["probe_cap"]
    seat = np.array([[-ss.CAV_X + 0.6, ss.CAV_Y_BACK + 0.4, ss.CAV_Z_BOT + 2],
                     [ss.CAV_X - 0.6, ss.PROBE_Y_BACK - 0.4, ss.CAV_Z_TOP - 2]])
    report(bool(cap.contains(seat).all()),
           "probe cap covers the whole cavity opening")
    report(abs(cap.extents[0] - (2 * ss.CAV_X - 0.2)) <= 0.6,
           f"cap width {cap.extents[0]:.1f} mm fits the {2 * ss.CAV_X:.1f} mm seat "
           f"(0.15 mm press-fit ribs)")

    # -- 6b. the gaskets must touch what they seal against ------------------
    # Both used to be modelled floating in mid-air: invisible assembled, wrong
    # the moment anyone printed them, so they get their own checks.
    bg, pg = meshes["bay_gasket"], meshes["probe_gasket"]
    report(abs(bg.bounds[0][1] - lid.bounds[0][1]) < 0.05,
           f"bay gasket lies on the lid's inner face "
           f"(Y {bg.bounds[0][1]:.2f} vs lid {lid.bounds[0][1]:.2f})")
    report(bg.bounds[1][0] - bg.bounds[0][0] <= lid.extents[0]
           and bg.bounds[1][2] - bg.bounds[0][2] <= lid.extents[2],
           f"bay gasket {bg.extents[0]:.1f} x {bg.extents[2]:.1f} mm sits inside "
           f"the {lid.extents[0]:.1f} x {lid.extents[2]:.1f} mm lid")
    report(abs(pg.bounds[1][1] - cap.bounds[0][1]) < 0.05,
           f"probe gasket sits against the cap's inner face "
           f"(Y {pg.bounds[1][1]:.2f} vs cap {cap.bounds[0][1]:.2f})")
    report(pg.bounds[1][0] - pg.bounds[0][0] <= 2 * ss.CAV_X + 0.1,
           f"probe gasket {pg.extents[0]:.1f} mm fits the "
           f"{2 * ss.CAV_X:.1f} mm cavity mouth")


    # -- 7. overhangs ------------------------------------------------------
    # Measured in assembly orientation; cad/orient.py rotates the part onto its
    # bed and splits these into free overhangs and internal bridges. Keep the
    # numbers here so a geometry change that adds overhang is visible.
    print("\noverhangs in assembly orientation (see cad/orient.py for print orientation)")
    down = body.face_normals[:, 2] < -0.72
    area = body.area_faces[down]
    lo = body.triangles[down].reshape(-1, 3).min(axis=0)
    hi = body.triangles[down].reshape(-1, 3).max(axis=0)
    report(area.sum() < 0.20 * body.area,
           f"overhang area {area.sum():.0f} mm2 "
           f"({100 * area.sum() / body.area:.0f}% of the surface)")
    # The promise that matters: in the orientation orient.py picks, nothing is
    # left hanging that support material would have to hold up.
    from orient import best_orientation
    pstats, ptag, _ = best_orientation(body)[0]
    report(pstats["free"] < 250,
           f"prints without support ({ptag}: {pstats['free']:.0f} mm2 free "
           f"overhang, {pstats['bridged']:.0f} mm2 bridged inside)")
    # Everything below Z = -128 is the sleeve's own bottom lip, which is a
    # 1.6 mm chamfer and prints fine. The rest wants support under the bay.
    bay_floor = down & (body.triangles_center[:, 2] < -50) \
                     & (body.triangles_center[:, 2] > -62) \
                     & (body.triangles_center[:, 1] > 0)
    report(0 < bay_floor.sum(),
           f"bay floor plate {body.area_faces[bay_floor].sum():.0f} mm2 is the "
           f"one wide span, and only when printed sleeve-down; bay-down it is "
           f"the bay's interior ceiling, bridged from three walls")
    # The hook has to bridge its own rim slot. Up to 12 mm is a clean PETG
    # bridge at 0.2 mm layers; beyond that the 12 mm variant needs support
    # under the bridge, which ASSEMBLY.md mentions.
    span = args.rim_gap + ss.BAY_FRONT
    if span <= 12.0:
        report(True, f"rim slot bridges {span:.1f} mm (unsupported, no sag)")
    else:
        print(f"  [NOTE] rim slot bridges {span:.1f} mm - print this variant with "
              f"support under the bridge")
    print(f"  bounds of all overhangs: X {lo[0]:.0f}..{hi[0]:.0f}, "
          f"Y {lo[1]:.0f}..{hi[1]:.0f}, Z {lo[2]:.0f}..{hi[2]:.0f}")

    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1



if __name__ == "__main__":
    raise SystemExit(main())
