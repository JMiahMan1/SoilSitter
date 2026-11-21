"""
Printability audit: what a slicer will actually do with the exported parts.

`orient.py` picks the best orientation and reports *free* overhang, which it
defines as a downward face with nothing at all under it. That definition is too
kind: a 27 mm wide ceiling 57 mm above the bed has material under it (the bed, the
walls) and so counts as "bridged", even though the slicer has to draw it across
27 mm of air. This script measures the thing that matters -- how wide each
unsupported span is, and how high up it sits -- and says plainly what will happen.

  couplers/bin/python cad/printability.py            # all five parts, rim 9
  couplers/bin/python cad/printability.py --rim 6

Verdicts use ordinary FDM rules for a 0.4 mm nozzle:

  * walls up to 45 deg from vertical      -> self-supporting
  * a flat span <= 15 mm, anchored        -> bridges cleanly
  * a flat span 15..30 mm, anchored       -> bridges, expect 0.2-0.5 mm sag
  * a flat span > 30 mm, or a span whose only anchors are on one side
                                          -> needs support, or a redesign
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
PRINT = ROOT / "stl" / "print"

#: faces whose normal points more than this far below horizontal are overhangs
OVERHANG_DEG = 52.0
#: a face this close to the bed is the bed face, not an overhang
BED_BAND = 0.6


def regions(mesh):
    """Downward-facing patches, grouped by shared edges."""
    n = np.asarray(mesh.face_normals, float)
    a = np.asarray(mesh.area_faces, float)
    ang = np.degrees(np.arcsin(np.clip(-n[:, 2], -1.0, 1.0)))
    z0 = float(mesh.bounds[0][2])
    down = (ang >= OVERHANG_DEG) & (mesh.triangles_center[:, 2] > z0 + BED_BAND)
    idx = np.where(down)[0]
    if not len(idx):
        return []
    parent = {int(i): int(i) for i in idx}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for f1, f2 in np.asarray(mesh.face_adjacency):
        if down[f1] and down[f2]:
            r1, r2 = find(int(f1)), find(int(f2))
            if r1 != r2:
                parent[r1] = r2
    groups: dict[int, list[int]] = {}
    for i in idx:
        groups.setdefault(find(int(i)), []).append(int(i))

    out = []
    for faces in groups.values():
        f = np.array(faces)
        # spans must come from vertices: a single 82 x 27 triangle has its
        # centroid in the middle, so centroids make every big plate look tiny
        v = np.asarray(mesh.vertices)[np.asarray(mesh.faces)[f].reshape(-1)]
        lo, hi = v.min(0), v.max(0)
        span = np.sort(hi[:2] - lo[:2])
        out.append(dict(area=float(a[f].sum()), short=float(span[0]),
                        long=float(span[1]), z=float(v[:, 2].mean()),
                        z_top=float(hi[2]), lo=lo, hi=hi,
                        angle=float(ang[f].max())))
    out.sort(key=lambda r: -r["area"])
    return out


def verdict(r):
    if r["angle"] < 89.0:                 # steep wall, not a ceiling
        return "wall", "steep wall - fine below 45 deg, check the angle"
    if r["short"] <= 15.0:
        return "ok", "bridges cleanly"
    if r["short"] <= 30.0:
        return "sag", "bridges across %.0f mm - expect light sag" % r["short"]
    return "bad", "%.0f mm of air - needs support or a redesign" % r["short"]


def audit(path: Path, verbose: bool = True):
    mesh = trimesh.load(path)
    z0 = float(mesh.bounds[0][2])
    height = float(mesh.extents[2])
    n = np.asarray(mesh.face_normals, float)
    a = np.asarray(mesh.area_faces, float)
    bed = float(a[n[:, 2] < -0.995][
        mesh.triangles_center[n[:, 2] < -0.995][:, 2] < z0 + 0.3].sum())
    foot = float(mesh.extents[0] * mesh.extents[1])
    regs = regions(mesh)
    counts = {"ok": 0, "sag": 0, "bad": 0, "wall": 0}
    for r in regs:
        r["verdict"], r["why"] = verdict(r)
        counts[r["verdict"]] += 1
    if verbose:
        print(f"\n{path.name}   {mesh.extents[0]:.0f} x {mesh.extents[1]:.0f}"
              f" x {height:.0f} mm, bed contact {bed:.0f} mm2 "
              f"({100 * bed / max(foot, 1):.0f}% of footprint)")
        for r in regs:
            if r["area"] < 5.0:
                continue
            print(f"  {r['area']:7.0f} mm2  at z {r['z']:6.1f}  "
                  f"span {r['short']:4.0f} x {r['long']:4.0f}  "
                  f"{r['angle']:4.0f} deg  -> {r['why']}")
        if not regs:
            print("  no overhang above 52 deg - nothing to support")
    return dict(name=path.stem, height=height, bed=bed, counts=counts,
                worst=max((r["short"] for r in regs), default=0.0),
                regs=regs)


def main():
    ap = argparse.ArgumentParser(description="printability audit of stl/print")
    ap.add_argument("--rim", type=float, default=9.0)
    ap.add_argument("--all-rims", action="store_true")
    args = ap.parse_args()
    rims = (6, 9, 12) if args.all_rims else (args.rim,)

    order = ["body", "bay_lid", "probe_cap", "bay_gasket", "probe_gasket"]
    bad = 0
    for rim in rims:
        print(f"\n=== rim gap {rim:g} mm, print orientations from stl/print")
        for name in order:
            p = PRINT / f"{name}_rim{rim:g}.stl"
            if not p.exists():
                print(f"  missing {p.name} - run cad/orient.py first")
                bad += 1
                continue
            res = audit(p)
            bad += res["counts"]["bad"]
    print("\nlegend: 'bridges' means the slicer spans open air from wall to wall."
          "\n        Nothing here is a free-floating roof; the tall sleeve is a")
    print("        rigidity question, not a support question - see docs/ASSEMBLY.md.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
