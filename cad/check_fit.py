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

#: name: (x0, x1, y0, y1, z0, z1, what)
HARDWARE = {
    "esp32-c3-supermini": (-38, -20, 4.5, 10.5, -32, -9.5,
                          "22.5 x 18 mm board, 6 mm + 2 mm header pins"),
    "lipo-103450": (-17, 17, 17.5, 27.5, -52, -2,
                    "10 x 34 x 50 mm pouch, 2000 mAh with protection"),
    "tp4056": (5, 30, 4.5, 10.5, -20, -1,
               "25 x 19 mm Type-C charger module"),
    "usb-pigtail": (-38, -22, 19.5, 29.5, -48, -32,
                    "M16 panel-mount USB-C barrel inside the bay"),
    "sensor-pcb": (-11.5, 11.5, -22.7, -21.1, -134, -36,
                   "98 x 23 x 1.6 mm capacitive probe"),
    "sensor-parts": (-11.5, 11.5, -22.7, -15.6, -134, -36,
                     "probe components, incl. the 3-pin connector"),
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
        inside = np.all(b[0] >= bay[0]) and np.all(b[1] <= bay[1])
        report(inside and clear.min() >= 0.4,
               f"{name:20s} fits, min wall clearance {clear.min():.1f} mm")

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
    pp = boxes["sensor-parts"]
    report(np.all(pc[0] >= probe[0]) and np.all(pc[1] <= probe[1]),
           "sensor PCB sits inside the probe cavity")
    report(np.all(pp[0] >= probe[0]) and np.all(pp[1] <= probe[1]),
           "sensor components clear the cap (no crushing of the connector)")
    report(probe[1, 0] - probe[0, 0] - (pc[1, 0] - pc[0, 0]) >= 1.0,
           "side clearance for the PCB >= 1 mm total")

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

    # -- 7. printability ---------------------------------------------------
    # The body prints as exported (probe sleeve down, bay up), so any face
    # steeper than 45 deg from vertical either lands on the plate or needs
    # support. Localise the support region so ASSEMBLY.md can name it.
    print("\nprintability (body, printed as exported)")
    down = body.face_normals[:, 2] < -0.72
    area = body.area_faces[down]
    lo = body.triangles[down].reshape(-1, 3).min(axis=0)
    hi = body.triangles[down].reshape(-1, 3).max(axis=0)
    report(area.sum() < 0.20 * body.area,
           f"overhang area {area.sum():.0f} mm2 "
           f"({100 * area.sum() / body.area:.0f}% of the surface)")
    # Everything below Z = -128 is the sleeve's own bottom lip, which is a
    # 1.6 mm chamfer and prints fine. The rest wants support under the bay.
    bay_floor = down & (body.triangles_center[:, 2] < -50) \
                     & (body.triangles_center[:, 2] > -62) \
                     & (body.triangles_center[:, 1] > 0)
    report(0 < bay_floor.sum(),
           f"bay floor overhang {body.area_faces[bay_floor].sum():.0f} mm2 at "
           f"Z {body.triangles_center[bay_floor][:, 2].min():.0f}.."
           f"{body.triangles_center[bay_floor][:, 2].max():.0f} mm, "
           f"Y {body.triangles_center[bay_floor][:, 1].min():.0f}.."
           f"{body.triangles_center[bay_floor][:, 1].max():.0f} mm "
           f"-> supports from the build plate")
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
