"""
The X=0 cutaway drawing: printed parts, the pot wall, the soil line and the real
hardware the plane cuts through. The photographed-looking views are in
cad/preview.py; this file is the technical drawing.

  docs/diagrams/section.png

    .venv-cad/bin/python cad/render.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
import trimesh.path  # noqa: F401  (Path2D is used by the section)
from matplotlib.patches import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soilsitter as ss  # noqa: E402
from check_fit import HARDWARE  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STL = ROOT / "stl"
OUT = ROOT / "docs" / "diagrams"

COLORS = {
    "body": (222, 219, 210),
    "bay_lid": (196, 122, 84),
    "probe_cap": (196, 122, 84),
    "pot": (176, 196, 206),
    "board": (38, 92, 66),
    "charger": (30, 60, 120),
    "cell": (70, 70, 78),
    "sensor": (150, 90, 160),
}


# ---------------------------------------------------------------------------
# z-buffer renderer
# ---------------------------------------------------------------------------
def look_at(eye, target, up=(0, 0, 1)):
    f = np.asarray(target, float) - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return np.stack([r, u, -f])


def render(meshes, eye, target, size=(1000, 1000), fov_mm=210.0,
           light=(-0.45, 0.55, 0.75), bg=(250, 250, 252)):
    W, H = size
    R = look_at(np.asarray(eye, float), np.asarray(target, float))
    scale = W / fov_mm
    zbuf = np.full(H * W, np.inf)
    cbuf = np.zeros((H * W, 3))
    L = np.asarray(light, float)
    L /= np.linalg.norm(L)
    Lv = R @ L
    for m, rgb in meshes:
        v = (m.vertices - target) @ R.T
        px = v[:, 0] * scale + W / 2
        py = -v[:, 1] * scale + H / 2
        pz = -v[:, 2]
        n = m.face_normals @ R.T
        keep = n[:, 2] > 0.02
        faces = m.faces[keep]
        shade = 0.45 + 0.55 * np.clip(n[keep] @ Lv, 0, 1)
        col = np.clip(np.asarray(rgb, float) / 255.0, 0, 1)[None, :] * shade[:, None]
        for (a, b, c), k in zip(faces, col):
            x0, x1 = int(min(px[a], px[b], px[c])), int(max(px[a], px[b], px[c])) + 1
            y0, y1 = int(min(py[a], py[b], py[c])), int(max(py[a], py[b], py[c])) + 1
            x0, x1 = max(x0, 0), min(x1, W)
            y0, y1 = max(y0, 0), min(y1, H)
            if x0 >= x1 or y0 >= y1:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1) + 0.5,
                                 np.arange(y0, y1) + 0.5)
            ax, ay = px[a], py[a]
            bx, by = px[b], py[b]
            cx, cy = px[c], py[c]
            d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(d) < 1e-9:
                continue
            w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / d
            w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / d
            w2 = 1.0 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any():
                continue
            depth = w0 * pz[a] + w1 * pz[b] + w2 * pz[c]
            idx = (np.arange(y0, y1)[:, None] * W + np.arange(x0, x1)[None, :])[inside]
            dsel = depth[inside]
            nearer = dsel < zbuf[idx]
            idx = idx[nearer]
            zbuf[idx] = dsel[nearer]
            cbuf[idx] = col[0]
    img = cbuf.reshape(H, W, 3)
    img[~np.isfinite(zbuf).reshape(H, W)] = np.asarray(bg) / 255.0
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def pot_meshes(rim_gap: float, depth: float = 95.0, height: float = 190.0):
    """A pot wall (4 mm) with a thicker rolled rim on top, and the soil."""
    wall = trimesh.creation.box(extents=(240, 4.0, height))
    wall.apply_translation((0, -2.0, -height / 2))
    rim = trimesh.creation.box(extents=(240, rim_gap, 3.0))
    rim.apply_translation((0, -rim_gap / 2, -1.5))
    soil = trimesh.creation.box(extents=(236, depth, 2.0))
    soil.apply_translation((0, -depth / 2, -26.0))
    return [(wall, COLORS["pot"]), (rim, COLORS["pot"]),
            (soil, (122, 96, 74))]


def hardware_meshes():
    out = []
    color = {"esp32": COLORS["board"], "tp4056": COLORS["charger"],
             "lipo": COLORS["cell"], "usb": (90, 96, 110),
             "sensor": COLORS["sensor"]}
    for name, (x0, x1, y0, y1, z0, z1, _) in HARDWARE.items():
        key = next(k for k in color if name.startswith(k))
        m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
        m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        out.append((m, color[key]))
    return out


def save(img, path):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(path)
    print(f"wrote {path.relative_to(ROOT)}")



# ---------------------------------------------------------------------------
# section drawing
# ---------------------------------------------------------------------------
def section_polygons(mesh, x=0.0):
    """Closed (Y, Z) polygons of the mesh's X=const cross-section.

    The section's own 3D vertices are used directly: ``to_planar`` re-centres
    the path in its own frame, which silently offsets the drawing.
    """
    sec = mesh.section(plane_origin=(x, 0, 0), plane_normal=(1, 0, 0))
    if sec is None:
        return []
    path = trimesh.path.Path2D(vertices=sec.vertices[:, [1, 2]],
                               entities=sec.entities)
    out = []
    for poly in path.polygons_full:
        out.append((np.asarray(poly.exterior.coords),
                    [np.asarray(r.coords) for r in poly.interiors]))
    return out


def draw_section(rim_gap: float, path: Path):
    body = trimesh.load(STL / f"body_rim{rim_gap:g}.stl")
    lid = trimesh.load(STL / f"bay_lid_rim{rim_gap:g}.stl")
    cap = trimesh.load(STL / f"probe_cap_rim{rim_gap:g}.stl")

    fig, ax = plt.subplots(figsize=(7.2, 10.5))
    for mesh, color, z in ((body, "#ddd9d0", 1), (lid, "#c47a54", 2),
                           (cap, "#c47a54", 2)):
        for ext, holes in section_polygons(mesh):
            ax.add_patch(Polygon(ext[:, :2], closed=True, facecolor=color,
                                 edgecolor="#555", lw=0.8, zorder=z))
            for hole in holes:
                ax.add_patch(Polygon(hole[:, :2], closed=True,
                                     facecolor="white", edgecolor="#555",
                                     lw=0.6, zorder=z + 0.1))

    ax.add_patch(Polygon([[0, -3], [-rim_gap, -3], [-rim_gap, 0], [0, 0]],
                         closed=True, facecolor="#b0c4ce", edgecolor="#5b7b8a",
                         lw=0.8, zorder=0.5))
    ax.add_patch(Polygon([[0, -3], [0, -160], [-4, -160], [-4, -3]],
                         closed=True, facecolor="#b0c4ce", edgecolor="#5b7b8a",
                         lw=0.8, zorder=0.5))
    ax.axhline(0, color="#5b7b8a", lw=0.8, ls="--", zorder=0.6)
    ax.axhline(-34, color="#7a6048", lw=1.0, ls=":", zorder=0.6)

    labels = {"esp32-c3-supermini": "SuperMini", "lipo-103450": "cell",
              "tp4056": "TP4056", "usb-pigtail": "USB-C",
              "sensor-pcb": "probe PCB", "sensor-parts": ""}
    for name, (x0, x1, y0, y1, z0, z1, _) in HARDWARE.items():
        if not (x0 <= 0.0 <= x1):
            continue          # this part is not on the X=0 plane
        ax.add_patch(plt.Rectangle((y0, z0), y1 - y0, z1 - z0,
                                   facecolor="#8fb4a0", edgecolor="#2f5c44",
                                   lw=0.8, zorder=3))
        if name == "sensor-pcb":
            ax.annotate("probe PCB + parts", (y0, (z0 + z1) / 2),
                        xytext=(-64, (z0 + z1) / 2), fontsize=8, va="center",
                        arrowprops=dict(arrowstyle="-", lw=0.6, color="#444"))
        elif labels[name]:
            ax.annotate(labels[name], ((y0 + y1) / 2, (z0 + z1) / 2),
                        fontsize=7.5, ha="center", va="center", color="#123",
                        zorder=4)

    ax.annotate("pot wall", (0, -120), xytext=(24, -120), fontsize=8,
                va="center", arrowprops=dict(arrowstyle="-", lw=0.6,
                                             color="#444"))
    ax.annotate("rim top (Z=0)", (0, 0), xytext=(24, 12), fontsize=8,
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#444"))
    ax.annotate("soil line", (-44, -34), xytext=(24, -48), fontsize=8,
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#7a6048"))
    ax.annotate("wire groove", (-12.0, -14.0), xytext=(18, -6), fontsize=8,
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#444"))

    ax.set_xlim(-70, 42)
    ax.set_ylim(-150, 30)
    ax.set_aspect("equal")
    ax.set_xlabel("Y (mm) - behind the pot -> +Y")
    ax.set_ylabel("Z (mm)")
    ax.grid(alpha=0.18, lw=0.5)
    ax.set_title(f"SoilSitter section at X=0 (rim gap {rim_gap:g} mm)\n"
                 "printed parts and the hardware the plane cuts", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


def main():
    """The cutaway drawing only: cad/preview.py owns the photographic views."""
    rim_gap = float(sys.argv[1]) if len(sys.argv) > 1 else ss.RIM_GAP
    draw_section(rim_gap, OUT / "section.png")


if __name__ == "__main__":
    main()
