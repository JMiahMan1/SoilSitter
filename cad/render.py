"""
The X=0 cutaway drawing: printed parts, the pot wall, the soil line and the real
hardware the plane cuts through. The photographed-looking views are in
cad/preview.py; this file is the technical drawing.

  docs/diagrams/section.png     the X=0 cutaway
  docs/diagrams/bay_layout.png   plan view of the open bay, lid off

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
             "ht7333": (94, 122, 62), "lipo": COLORS["cell"],
             "usb": (90, 96, 110), "sensor-conn": (120, 96, 140),
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
              "tp4056": "TP4056", "ht7333": "LDO", "usb-pigtail": "USB-C",
              "sensor-pcb": "probe PCB", "sensor-smd": "",
              "sensor-connector": ""}
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
        elif labels.get(name):
            ax.annotate(labels[name], ((y0 + y1) / 2, (z0 + z1) / 2),
                        fontsize=7.5, ha="center", va="center", color="#123",
                        zorder=4)

    ax.annotate("pot wall", (0, -120), xytext=(-9, -126), fontsize=8,
                va="center", ha="right",
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#444"))
    ax.annotate("rim top (Z=0)", (0, 0), xytext=(24, 12), fontsize=8,
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#444"))
    ax.annotate("soil line", (-44, -34), xytext=(-68, -30), fontsize=8,
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


def draw_layout(rim_gap: float, path: Path):
    """Plan view into the open bay: what goes where.

    The bay is 27 mm deep, so a flat projection would show the cell on top of the
    boards. Parts nearer the lid are solid; parts deeper in the bay are hatched,
    and every label carries its Y band.
    """
    fig, ax = plt.subplots(figsize=(9.8, 7.2))

    half, wall = ss.BAY_W / 2, ss.WALL_SIDE
    z0, z1 = ss.BAY_BOT + ss.WALL_BOT, ss.BAY_TOP - ss.TOP_WALL
    ax.add_patch(plt.Rectangle((-half, ss.BAY_BOT), ss.BAY_W, ss.BAY_H,
                               facecolor="#e4e0d6", edgecolor="#8b867c", lw=1.0))
    ax.add_patch(plt.Rectangle((-half + wall, z0), 2 * (half - wall), z1 - z0,
                               facecolor="#fbfaf7", edgecolor="#6f6a60", lw=1.0))

    # lid screw bosses first, so they never cover a part
    for sx in (-ss.BOSS_X, ss.BOSS_X):
        ax.add_patch(plt.Rectangle((sx - 5, ss.LID_BOT_SCREW_Z - 5), 10, 10,
                                   facecolor="none", edgecolor="#a8341f",
                                   lw=1.0, ls=(0, (3, 2)), zorder=2))
        ax.plot([sx], [ss.LID_TOP_SCREW_Z], marker="+", ms=9, mew=1.4,
                color="#a8341f", zorder=2)

    # deep layer: behind the boards
    deep = {"lipo": ("#b9b3a6", "//"), "usb": ("#c9c6c0", "xx")}
    for name, (px0, px1, _, _, pz0, pz1, _) in HARDWARE.items():
        key = next((k for k in deep if name.startswith(k)), None)
        if key is None:
            continue
        fill, hatch = deep[key]
        ax.add_patch(plt.Rectangle((px0, pz0), px1 - px0, pz1 - pz0,
                                   facecolor=fill, edgecolor="#4a4a52", lw=1.0,
                                   hatch=hatch, alpha=0.85, zorder=3))

    fill_deep_txt = "#2b2b33"
    ax.text(-0.5, -26, "103450 cell\n35 x 52\nY 17-28", color=fill_deep_txt,
            fontsize=9, ha="center", va="center", zorder=6, linespacing=1.35,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.75))

    # near layer: taped to the lid
    near = {"esp32": ((38, 92, 66), "SuperMini\n22.5 x 18\nY 3-8"),
            "tp4056": ((30, 60, 120), "TP4056\n29 x 17\nY 3-7"),
            "ht7333": ((93, 122, 62), "")}
    for name, (px0, px1, _, _, pz0, pz1, _) in HARDWARE.items():
        key = next((k for k in near if name.startswith(k)), None)
        if key is None:
            continue
        rgb, text = near[key]
        ax.add_patch(plt.Rectangle((px0, pz0), px1 - px0, pz1 - pz0,
                                   facecolor=[c / 255 for c in rgb],
                                   edgecolor="#20242a", lw=0.9, zorder=4))
        if text:
            ax.text((px0 + px1) / 2, (pz0 + pz1) / 2, text, color="white",
                    fontsize=8, ha="center", va="center", zorder=6,
                    linespacing=1.35)

    ldo = HARDWARE["ht7333"]
    ax.annotate("HT7333 LDO\nY 3-7", ((ldo[0] + ldo[1]) / 2, (ldo[4] + ldo[5]) / 2),
                xytext=(-16, -12), fontsize=7.5, color="#2d4a18", zorder=7,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.85),
                arrowprops=dict(arrowstyle="-", lw=0.8, color="#3d5a20"))

    r = ss.CHARGE_PORT_D / 2
    ax.add_patch(plt.Circle((ss.CHARGE_PORT_X, ss.CHARGE_PORT_Z), r, fill=False,
                            edgecolor="#33404a", lw=1.3, ls=(0, (2, 2)), zorder=5))
    ax.annotate("M16 charge port\nthrough the back wall",
                (ss.CHARGE_PORT_X + r * 0.72, ss.CHARGE_PORT_Z),
                xytext=(ss.CHARGE_PORT_X, ss.CHARGE_PORT_Z - 13), fontsize=7.5,
                color="#33404a", zorder=7, ha="center",
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.85),
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#33404a"))

    ax.annotate("probe cable notch (X 0)", (0.0, z1), xytext=(16, 5), fontsize=7.5,
                color="#444", zorder=7,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.85),
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#444"))
    ax.annotate("lid screw boss x2\n(+ = top wall screws)",
                (-ss.BOSS_X + 5, ss.LID_BOT_SCREW_Z - 5),
                xytext=(-half - 7.5, ss.BAY_BOT - 4.0), fontsize=7.5,
                color="#8d2b19", zorder=7,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.85),
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#a8341f"))

    ax.text(0, z0 - 8.0,
            "solid = taped to the lid    hatched = deeper in the bay (cell, pigtail)",
            fontsize=8, ha="center", va="top", color="#4d4a44")

    ax.set_xlim(-half - 10, half + 6)
    ax.set_ylim(ss.BAY_BOT - 14, ss.BAY_TOP + 2.5)
    ax.set_aspect("equal")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Z (mm)")
    ax.grid(alpha=0.15, lw=0.5)
    ax.set_title(f"Bay layout with the lid off (rim gap {rim_gap:g} mm): "
                 f"{2 * (half - wall):.0f} x {z1 - z0:.0f} mm against the lid\n"
                 "the lid carries the boards, so this is its inner face",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


def main():
    """The cutaway drawing only: cad/preview.py owns the photographic views."""
    rim_gap = float(sys.argv[1]) if len(sys.argv) > 1 else ss.RIM_GAP
    draw_section(rim_gap, OUT / "section.png")
    draw_layout(rim_gap, OUT / "bay_layout.png")


if __name__ == "__main__":
    main()
