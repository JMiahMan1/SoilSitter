"""
Print orientation: pick the orientation each part should be sliced in, and export
print-ready STLs.

The `stl/` files are in *assembly* orientation (they have to be, so the previews
and the fit checks line up). This writes `stl/print/` with the same parts rotated
so the largest flat face is on the bed, plus a manifest of what each one needs.

Scoring, per candidate orientation (the 24 axis-aligned ones):

  * overhang area   - faces steeper than 45 deg from vertical, in mm^2
  * support height  - the mean height of those faces above the bed, a proxy for
                      how much support material they cost
  * contact area    - the flat area actually touching the bed (bed adhesion)
  * height          - tall thin prints wobble and fail

    .venv-cad/bin/python cad/orient.py                 # rim 9
    .venv-cad/bin/python cad/orient.py --rim-gap 6
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
STL = ROOT / "stl"
OUT = STL / "print"

PARTS = ("body", "bay_lid", "probe_cap", "bay_gasket", "probe_gasket")


def axis_rotations():
    """The 24 axis-aligned orientations as (name, 3x3 matrix)."""
    from itertools import permutations, product
    out = []
    for perm in permutations(range(3)):
        for signs in product((1, -1), repeat=3):
            m = np.zeros((3, 3))
            for row, col in enumerate(perm):
                m[row, col] = signs[row]
            if round(np.linalg.det(m)) != 1:
                continue
            out.append((f"{perm}{signs}", m))
    return out


def score(mesh, R):
    v = np.asarray(mesh.vertices, float) @ R.T
    n = np.asarray(mesh.face_normals, float) @ R.T
    a = np.asarray(mesh.area_faces, float)
    c = np.asarray(mesh.triangles_center, float) @ R.T
    z0, z1 = v[:, 2].min(), v[:, 2].max()
    height = z1 - z0
    down = (n[:, 2] < -0.72) & (c[:, 2] > z0 + 0.6)
    overhang = float(a[down].sum())
    # Split the overhang: a face with material below it is a step or an internal
    # bridge (support cannot or should not reach it); a face with nothing below
    # it is a free overhang that support material has to carry.
    free = overhang
    if down.any():
        rot = mesh.copy()
        pivot = np.eye(4)
        pivot[:3, :3] = R
        rot.apply_transform(pivot)
        origin = rot.triangles_center[down] - np.array([0.0, 0.0, 0.05])
        dirs = np.tile([0.0, 0.0, -1.0], (len(origin), 1))
        below = rot.ray.intersects_any(origin, dirs)
        free = float(a[down][~below].sum())
    drop = float((c[down, 2] - z0).mean()) if down.any() else 0.0
    flat = n[:, 2] < -0.995
    contact = float(a[flat & (c[:, 2] < z0 + 0.35)].sum())
    footprint = (v[:, 0].max() - v[:, 0].min()) * (v[:, 1].max() - v[:, 1].min())
    # Height over the *narrow* footprint dimension: a 106 mm plate standing on its
    # 2.5 mm edge has no overhangs at all, and still falls over.
    fx = v[:, 0].max() - v[:, 0].min()
    fy = v[:, 1].max() - v[:, 1].min()
    slenderness = height / max(min(fx, fy), 1.0)
    score = (overhang * (0.35 + drop / max(height, 1.0))
             + 3.0 * height
             + 250.0 * max(0.0, slenderness - 1.0) ** 2
             - 0.25 * min(contact, 4000.0))
    if footprint > 0 and contact < 0.02 * footprint:
        score += 40000.0          # standing on an edge or a curve
    return {
        "score": score, "overhang": overhang, "free": free, "drop": drop,
        "contact": contact, "height": height, "footprint": footprint,
        "z0": z0, "bridged": overhang - free,
    }


def best_orientation(mesh):
    scored = [(score(mesh, R), name, R) for name, R in axis_rotations()]
    scored.sort(key=lambda t: t[0]["score"])
    return scored


def orient_part(path: Path, name: str, verbose: bool = False):
    mesh = trimesh.load(path)
    ranked = best_orientation(mesh)
    stats, tag, R = ranked[0]
    out = mesh.copy()
    out.apply_transform(np.block([[R, np.zeros((3, 1))], [np.zeros((1, 3)), 1.0]]))
    out.apply_translation((0, 0, -stats["z0"]))
    if verbose:
        print(f"  {name}: {len(ranked)} orientations, top 3")
        for s, t, _ in ranked[:3]:
            print(f"    {t}  score {s['score']:9.0f}  overhang {s['overhang']:7.0f} mm2"
                  f"  h {s['height']:5.1f} mm  contact {s['contact']:7.0f} mm2")
    OUT.mkdir(parents=True, exist_ok=True)
    out.export(OUT / f"{name}_{path.stem.split('_')[-1]}.stl")
    return stats, out


def main():
    ap = argparse.ArgumentParser(description="export print-oriented STLs")
    ap.add_argument("--rim-gap", type=float, default=9.0)
    args = ap.parse_args()
    sfx = f"rim{args.rim_gap:g}"

    print(f"print orientation for rim {args.rim_gap:g} mm "
          f"(bed plate {OUT.relative_to(ROOT)}/)")
    manifest = {}
    for part in PARTS:
        src = STL / f"{part}_{sfx}.stl"
        if not src.exists():
            print(f"  {part}: {src.name} missing")
            continue
        stats, mesh = orient_part(src, part)
        bb = mesh.extents
        manifest[part] = {
            "file": f"{part}_{sfx}.stl",
            "bbox_on_bed_mm": [round(bb[0], 1), round(bb[1], 1), round(bb[2], 1)],
            "overhang_mm2": round(stats["overhang"]),
            "needs_support_mm2": round(stats["free"]),
            "bridged_mm2": round(stats["bridged"]),
            "bed_contact_mm2": round(stats["contact"]),
        }
        note = ("no support needed" if stats["free"] < 250 else
                f"{stats['free']:.0f} mm2 of support, "
                f"{stats['bridged']:.0f} mm2 bridged/internal")
        print(f"  {part:14s} {bb[0]:6.1f} x {bb[1]:6.1f} x {bb[2]:5.1f} mm   {note}")

    (OUT / f"manifest_{sfx}.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nwrote {len(manifest)} print STLs + manifest to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
