"""
Preview renders for SoilSitter - what the device actually looks like.

  docs/diagrams/hero.png       the three printed parts, assembled, studio shot
  docs/diagrams/exploded.png   the same parts pulled apart, labelled
  docs/diagrams/mounted.png    clipped on a pot, from the device's side
  docs/diagrams/room_view.png  the same pot from the room: nothing to see
  docs/diagrams/views.png      front / side / top orthographic sheet
  docs/diagrams/section.png    (render.py) the X=0 section with hardware

A small numpy z-buffer rasteriser: orthographic camera, smooth per-corner normals
with a hard-edge threshold, Lambert + rim light, 3x supersampling and a soft studio
background. No GPU, no window, no external renderer.

    .venv-cad/bin/python cad/preview.py
    .venv-cad/bin/python cad/preview.py --rim-gap 12
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
OUT = ROOT / "docs" / "diagrams"

#: Filament-ish colours, sRGB 0-255.
C_BODY = (226, 222, 212)
C_ACCENT = (198, 120, 78)
C_GASKET = (70, 74, 82)
C_POT = (176, 196, 206)
C_SOIL = (104, 82, 62)
C_LEAF = (74, 122, 78)
C_STEM = (96, 116, 66)
C_BOARD = (34, 84, 60)
C_CELL = (64, 66, 74)
C_METAL = (150, 154, 162)


# ---------------------------------------------------------------------------
# normals
# ---------------------------------------------------------------------------
def corner_normals(mesh, angle_deg: float = 32.0):
    """Per-corner normals, averaged only across faces within `angle_deg`.

    STL has no shared vertices, so trimesh's merge gives hard edges averaged
    into mush. Clustering by position and skipping normals that diverge keeps
    fillets smooth and corners sharp.
    """
    n = np.asarray(mesh.face_normals, float)
    v = np.asarray(mesh.vertices, float)
    faces = np.asarray(mesh.faces)
    key = np.round(v * 200).astype(np.int64)          # 0.005 mm buckets
    _, group = np.unique(key, axis=0, return_inverse=True)
    order = np.argsort(group, kind="stable")
    bounds = np.searchsorted(group[order], np.arange(group.max() + 2))
    cos_lim = np.cos(np.radians(angle_deg))

    out = np.empty((len(faces), 3, 3), float)
    for f, tri in enumerate(faces):
        nf = n[f]
        for k, vi in enumerate(tri):
            lo, hi = bounds[group[vi]], bounds[group[vi] + 1]
            nb = order[lo:hi]
            adj = n[nb]
            keep = adj @ nf > cos_lim
            acc = (adj[keep] * np.maximum(adj[keep] @ nf, 1e-3)[:, None]).sum(0)
            norm = np.linalg.norm(acc)
            out[f, k] = acc / norm if norm > 1e-9 else nf
    return out


# ---------------------------------------------------------------------------
# camera
# ---------------------------------------------------------------------------
def look_at(eye, target, up=(0, 0, 1)):
    f = np.asarray(target, float) - np.asarray(eye, float)
    f /= np.linalg.norm(f)
    r = np.cross(f, np.asarray(up, float))
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return np.stack([r, u, -f])


# ---------------------------------------------------------------------------
# framing, shared by the renderer and the labels
# ---------------------------------------------------------------------------
def fit_params(parts, eye, target, size, margin=0.075, ss=1):
    """(rotation, pixels-per-mm, centre-x, centre-y) that fit the parts."""
    W, H = size
    R = look_at(eye, target)
    allv = np.vstack([np.asarray(m.vertices, float) for m, _ in parts])
    proj = (allv - np.asarray(target, float)) @ R.T
    x0, x1 = proj[:, 0].min(), proj[:, 0].max()
    y0, y1 = proj[:, 1].min(), proj[:, 1].max()
    span = max(x1 - x0, (y1 - y0) * W / H)
    span = max(span, 1e-6) / (1.0 - 2 * margin)
    return R, (W * ss) / span, (x0 + x1) / 2, (y0 + y1) / 2


def to_px(pt, eye, target, size, margin=0.075, parts=None, ss=1):
    """Project a model-space point to image pixels for the same framing."""
    R, scale, cx, cy = fit_params(parts, eye, target, size, margin, ss)
    v = (np.asarray(pt, float) - np.asarray(target, float)) @ R.T
    return ((v[0] - cx) * scale + size[0] * ss / 2,
            -(v[1] - cy) * scale + size[1] * ss / 2)


def render(parts, *, eye, target, size=(1280, 1040), ss=2, margin=0.075,
           bg_top=(253, 253, 251), bg_bottom=(226, 228, 232),
           key_dir=(-0.42, 0.52, 0.74), fill_dir=(0.60, -0.30, 0.44),
           shadow=None, outline=True, ghost=None):
    """Orthographic z-buffer render of [(mesh, rgb)] -> uint8 (H, W, 3).

    `shadow` is an optional dict(centre=(x, y) in mm, radii=(rx, ry), strength)
    painted into the background before the geometry.
    """
    W, H = size
    W2, H2 = W * ss, H * ss
    frame_parts = parts + [(m, (0, 0, 0)) for m, _, _ in (ghost or [])]
    R, scale, cx, cy = fit_params(frame_parts, eye, target, size, margin, ss)

    # background: vertical gradient plus a soft vignette
    yy = (np.arange(H2)[:, None] + 0.5) / H2
    grad = (np.asarray(bg_top, float) / 255.0)[None, :] * (1 - yy[..., None]) \
        + (np.asarray(bg_bottom, float) / 255.0)[None, :] * yy[..., None]
    img = np.repeat(grad, W2, axis=1)
    gx = (np.arange(W2)[None, :] + 0.5) / W2 - 0.5
    gy = (np.arange(H2)[:, None] + 0.5) / H2 - 0.5
    vig = 1.0 - 0.16 * np.clip(gx ** 2 / 0.5 + (gy * 1.15) ** 2 / 0.62, 0, 1)
    img *= vig[..., None]


    if shadow:
        sx, sy = shadow.get("radii", (60.0, 60.0))
        px_c = (shadow["centre"][0] - cx) * scale + W2 / 2
        py_c = -(shadow["centre"][1] - cy) * scale + H2 / 2
        rx, ry = max(sx * scale, 1.0), max(sy * scale, 1.0)
        xr = (np.arange(W2)[None, :] + 0.5 - px_c) / rx
        yr = (np.arange(H2)[:, None] + 0.5 - py_c) / ry
        fall = np.exp(-2.4 * (xr ** 2 + yr ** 2))
        img *= (1.0 - shadow.get("strength", 0.30) * fall)[..., None]

    zbuf = np.full(H2 * W2, np.inf, np.float32)
    # Camera-space lights: -x is screen left, +y is up, +z is towards the camera.
    L1v = np.asarray(key_dir, float) / np.linalg.norm(key_dir)
    L2v = np.asarray(fill_dir, float) / np.linalg.norm(fill_dir)
    up_cam = R @ np.array([0.0, 0.0, 1.0])
    Hv = L1v + np.array([0.0, 0.0, 1.0])
    Hv /= np.linalg.norm(Hv)
    flat_img = img.reshape(-1, 3)

    for mesh, rgb in parts:
        base = np.asarray(rgb, float) / 255.0
        v = (np.asarray(mesh.vertices, float) - np.asarray(target, float)) @ R.T
        px = (v[:, 0] - cx) * scale + W2 / 2
        py = -(v[:, 1] - cy) * scale + H2 / 2
        pz = -v[:, 2]
        nrm = corner_normals(mesh) @ R.T
        faces = np.asarray(mesh.faces)
        lit = nrm.mean(axis=1)[:, 2] > 0.015
        faces, nrm = faces[lit], nrm[lit]

        for tri, na, nb, nc in zip(faces, nrm[:, 0], nrm[:, 1], nrm[:, 2]):
            a, b, c = tri
            xa, xb, xc = px[a], px[b], px[c]
            ya, yb, yc = py[a], py[b], py[c]
            ix0 = max(int(min(xa, xb, xc)), 0)
            ix1 = min(int(max(xa, xb, xc)) + 1, W2)
            iy0 = max(int(min(ya, yb, yc)), 0)
            iy1 = min(int(max(ya, yb, yc)) + 1, H2)
            if ix0 >= ix1 or iy0 >= iy1:
                continue
            xs, ys = np.meshgrid(np.arange(ix0, ix1) + 0.5,
                                 np.arange(iy0, iy1) + 0.5)
            det = (yb - yc) * (xa - xc) + (xc - xb) * (ya - yc)
            if abs(det) < 1e-9:
                continue
            w0 = ((yb - yc) * (xs - xc) + (xc - xb) * (ys - yc)) / det
            w1 = ((yc - ya) * (xs - xc) + (xa - xc) * (ys - yc)) / det
            w2 = 1.0 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any():
                continue
            depth = w0 * pz[a] + w1 * pz[b] + w2 * pz[c]
            flat = (np.arange(iy0, iy1)[:, None] * W2
                    + np.arange(ix0, ix1)[None, :])[inside]
            dsel = depth[inside]
            near = dsel < zbuf[flat]
            if not near.any():
                continue
            flat, dsel = flat[near], dsel[near]
            bw0, bw1, bw2 = w0[inside][near], w1[inside][near], w2[inside][near]
            zbuf[flat] = dsel
            nd = bw0[:, None] * na + bw1[:, None] * nb + bw2[:, None] * nc
            nd /= np.maximum(np.linalg.norm(nd, axis=1), 1e-9)[:, None]
            lam = np.clip(nd @ L1v, 0, 1)
            fil = np.clip(nd @ L2v, 0, 1)
            sky = 0.22 + 0.22 * np.clip((nd @ up_cam) * 0.5 + 0.5, 0, 1)
            spec = 0.16 * np.clip(nd @ Hv, 0, 1) ** 30
            shade = sky + 0.74 * lam + 0.14 * fil
            flat_img[flat] = base[None, :] * shade[:, None] + spec[:, None]

    if ghost:
        galpha = np.zeros(H2 * W2, np.float32)
        gcol = np.zeros((H2 * W2, 3), np.float32)
        for mesh, rgb, alpha in ghost:
            base = np.asarray(rgb, float) / 255.0
            v = (np.asarray(mesh.vertices, float) - np.asarray(target, float)) @ R.T
            px = (v[:, 0] - cx) * scale + W2 / 2
            py = -(v[:, 1] - cy) * scale + H2 / 2
            pz = -v[:, 2]
            nrm = corner_normals(mesh) @ R.T
            faces = np.asarray(mesh.faces)
            lit = nrm.mean(axis=1)[:, 2] > 0.015
            faces, nrm = faces[lit], nrm[lit]
            for tri, na, nb, nc in zip(faces, nrm[:, 0], nrm[:, 1], nrm[:, 2]):
                a, b, c = tri
                xa, xb, xc = px[a], px[b], px[c]
                ya, yb, yc = py[a], py[b], py[c]
                ix0 = max(int(min(xa, xb, xc)), 0)
                ix1 = min(int(max(xa, xb, xc)) + 1, W2)
                iy0 = max(int(min(ya, yb, yc)), 0)
                iy1 = min(int(max(ya, yb, yc)) + 1, H2)
                if ix0 >= ix1 or iy0 >= iy1:
                    continue
                xs, ys = np.meshgrid(np.arange(ix0, ix1) + 0.5,
                                     np.arange(iy0, iy1) + 0.5)
                det = (yb - yc) * (xa - xc) + (xc - xb) * (ya - yc)
                if abs(det) < 1e-9:
                    continue
                w0 = ((yb - yc) * (xs - xc) + (xc - xb) * (ys - yc)) / det
                w1 = ((yc - ya) * (xs - xc) + (xa - xc) * (ys - yc)) / det
                w2 = 1.0 - w0 - w1
                inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
                if not inside.any():
                    continue
                depth = w0 * pz[a] + w1 * pz[b] + w2 * pz[c]
                flat = (np.arange(iy0, iy1)[:, None] * W2
                        + np.arange(ix0, ix1)[None, :])[inside]
                dsel = depth[inside]
                front = dsel <= zbuf[flat] + 0.5
                if not front.any():
                    continue
                flat, dsel = flat[front], dsel[front]
                bw0, bw1, bw2 = w0[inside][front], w1[inside][front], w2[inside][front]
                nd = bw0[:, None] * na + bw1[:, None] * nb + bw2[:, None] * nc
                nd /= np.maximum(np.linalg.norm(nd, axis=1), 1e-9)[:, None]
                shade = (0.45 + 0.55 * np.clip(nd @ L1v, 0, 1))[:, None]
                gcol[flat] = base[None, :] * shade
                galpha[flat] = np.maximum(galpha[flat], alpha)

    img = np.clip(flat_img.reshape(H2, W2, 3), 0, 1)
    if ghost:
        a = galpha.reshape(H2, W2, 1)
        img = img * (1 - a) + gcol.reshape(H2, W2, 3) * a
    img = (img.reshape(H, ss, W, ss, 3).mean(axis=(1, 3)) * 255).astype(np.uint8)
    if outline:
        img = add_outline(img)
    return img


def add_outline(img, strength=0.10):
    """Darken the silhouette by a pixel: reads as a drawing, still a photo."""
    m = (img.astype(np.int16).sum(2) < 720).astype(np.float32)   # not background
    er = m.copy()
    er[1:, :] *= m[:-1, :]
    er[:-1, :] *= m[1:, :]
    er[:, 1:] *= m[:, :-1]
    er[:, :-1] *= m[:, 1:]
    edge = np.clip(m - er, 0, 1)[..., None]
    out = img.astype(np.float32) * (1 - strength * edge)
    return np.clip(out, 0, 255).astype(np.uint8)


def save(img, name):
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    Image.fromarray(img).save(p)
    print(f"wrote {p.relative_to(ROOT)}  {img.shape[1]}x{img.shape[0]}")
    return p




# ---------------------------------------------------------------------------
# geometry: the device and a pot to hang it on
# ---------------------------------------------------------------------------
def load(part: str, rim_gap: float):
    return trimesh.load(STL / f"{part}_rim{rim_gap:g}.stl")


PART_COLOURS = {
    "body": C_BODY,
    "bay_lid": C_ACCENT,
    "probe_cap": C_ACCENT,
    "bay_gasket": C_GASKET,
    "probe_gasket": C_GASKET,
}


def device_parts(rim_gap: float, explode: dict | None = None):
    """[(mesh, colour)] for the five printed parts, optionally pulled apart."""
    out = []
    for part, colour in PART_COLOURS.items():
        m = load(part, rim_gap)
        off = (explode or {}).get(part)
        if off is not None:
            m = m.copy()
            m.apply_translation(off)
        out.append((m, colour))
    return out


def pot_parts(rim_gap: float, r_out: float = 74.0, height: float = 150.0,
              soil_top: float = -30.0):
    """Pot shell (open top), bottom disc and soil, in the device's coordinates.

    The pot's near outer wall sits at Y = 0 and its inner wall at Y = -rim_gap,
    which is exactly where the hook's leg hangs.
    """
    outer = trimesh.creation.cylinder(radius=r_out, height=height, sections=160)
    inner = trimesh.creation.cylinder(radius=r_out - rim_gap, height=height + 20,
                                      sections=160)
    shell = trimesh.boolean.difference([outer, inner])
    base = trimesh.creation.cylinder(radius=r_out, height=8, sections=160)
    soil = trimesh.creation.cylinder(radius=r_out - rim_gap - 0.6, height=14,
                                     sections=160)
    shell.apply_translation((0, -r_out, -height / 2))
    base.apply_translation((0, -r_out, -height + 4))
    soil.apply_translation((0, -r_out, soil_top - 7))
    return [(shell, C_POT), (base, C_POT), (soil, C_SOIL)]


def plant_parts(r_out: float = 74.0, soil_top: float = -30.0, leaves: int = 9,
                seed: int = 4):
    """A believable houseplant: stems as cylinders, leaves as squashed spheres."""
    rng = np.random.default_rng(seed)
    axis = np.array([0.0, -r_out, 0.0])
    out = []
    for i in range(leaves):
        ang = 2 * np.pi * i / leaves + rng.normal(0, 0.18)
        rad = rng.uniform(16, 40)
        base = axis + np.array([rad * np.cos(ang), rad * np.sin(ang), soil_top])
        span = rng.uniform(34, 84)
        lean = np.array([np.cos(ang), np.sin(ang), 0.0]) * rng.uniform(6, 22)
        top = base + lean + np.array([0.0, 0.0, span])
        d = top - base
        stem = trimesh.creation.cylinder(radius=1.5, height=np.linalg.norm(d),
                                         sections=10)
        axis_r = np.cross([0.0, 0.0, 1.0], d)
        if np.linalg.norm(axis_r) > 1e-9:
            ang_r = np.arccos(np.clip(d[2] / np.linalg.norm(d), -1, 1))
            stem.apply_transform(trimesh.transformations.rotation_matrix(
                ang_r, axis_r / np.linalg.norm(axis_r)))
        stem.apply_translation(base + d / 2)
        out.append((stem, C_STEM))
        leaf = trimesh.creation.icosphere(subdivisions=4, radius=1.0)
        sx, sy, sz = rng.uniform(15, 22), rng.uniform(1.8, 2.6), rng.uniform(8, 12)
        leaf.apply_transform(np.diag([sx, sy, sz, 1.0]))
        leaf.apply_transform(trimesh.transformations.rotation_matrix(
            rng.uniform(-40, -14) * np.pi / 180, [0, 1, 0]))
        leaf.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 0, 1]))
        leaf.apply_translation(top + np.array([0.0, 0.0, sz * 0.55]))
        out.append((leaf, C_LEAF))
    return out


def hardware_parts():
    """The real electronics, from the fit check's own boxes."""
    from check_fit import HARDWARE
    out = []
    for name, (x0, x1, y0, y1, z0, z1, _) in HARDWARE.items():
        colour = (C_BOARD if name.startswith("esp32") else
                  C_METAL if name.startswith("usb") else
                  C_CELL if name.startswith("lipo") else
                  (28, 58, 116) if name.startswith("tp") else (146, 92, 158))
        m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
        m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        out.append((m, colour))
    return out


# ---------------------------------------------------------------------------
# labels and compositing
# ---------------------------------------------------------------------------
def _font(size: int):
    from PIL import ImageFont
    import matplotlib.font_manager as fm
    return ImageFont.truetype(fm.findfont("DejaVu Sans"), size)


def annotate(img, parts, eye, target, items, size=None, margin=0.075,
             font_px=26, colour=(38, 42, 48)):
    """Draw leader lines and text on a rendered image.

    `items` is [(text, anchor_xyz, (label_x_frac, label_y_frac))].
    """
    from PIL import Image, ImageDraw
    H, W = img.shape[:2]
    size = size or (W, H)
    sx, sy = W / size[0], H / size[1]
    im = Image.fromarray(img).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    font = _font(font_px)
    for item in items:
        text, anchor = item[0], item[1]
        ax, ay = to_px(anchor, eye, target, size, margin, parts)
        if len(item) > 2:
            lx, ly = item[2][0] * W, item[2][1] * H
        else:                       # no position given: label above the anchor
            lx, ly = ax * sx, ay * sy - font_px * 1.6
        d.line([(ax * sx, ay * sy), (lx, ly)], fill=colour + (150,), width=2)
        d.ellipse([ax * sx - 4, ay * sy - 4, ax * sx + 4, ay * sy + 4],
                  fill=colour + (220,))
        tw = d.textlength(text, font=font)
        pad = 8
        left = lx if lx < W / 2 else lx - tw
        box = [left - pad, ly - font_px * 0.85, left + tw + pad, ly + font_px * 0.6]
        d.rounded_rectangle(box, radius=6, fill=(255, 255, 255, 205),
                            outline=colour + (60,), width=1)
        d.text((left, ly - font_px * 0.62), text, font=font, fill=colour)
    return np.asarray(im)


def contact_sheet(panels, titles, name, gap=14, bg=(246, 246, 244), title_px=30):
    """Tile rendered panels left-to-right with a caption under each."""
    from PIL import Image, ImageDraw
    h = max(p.shape[0] for p in panels)
    w = sum(p.shape[1] for p in panels) + gap * (len(panels) - 1)
    sheet = Image.new("RGB", (w, h + 52), bg)
    x = 0
    d = ImageDraw.Draw(sheet)
    font = _font(title_px)
    for p, title in zip(panels, titles):
        sheet.paste(Image.fromarray(p), (x, 0))
        tw = d.textlength(title, font=font)
        d.text((x + (p.shape[1] - tw) / 2, h + 12), title, font=font,
               fill=(60, 64, 70))
        x += p.shape[1] + gap
    p = OUT / name
    sheet.save(p)
    print(f"wrote {p.relative_to(ROOT)}  {sheet.size[0]}x{sheet.size[1]}")
    return p


# ---------------------------------------------------------------------------
# scenes
# ---------------------------------------------------------------------------
def rim_ghost(rim_gap: float, r_out: float = 74.0, z0: float = -34.0, z1: float = 3.0,
              half_width: float = 72.0):
    """The near arc of pot wall, drawn faintly in the hero shot.

    A full ring reads as a hoop the device is floating inside; a 140-degree arc
    reads as the wall it is hanging on.
    """
    outer = trimesh.creation.cylinder(radius=r_out, height=z1 - z0, sections=140)
    inner = trimesh.creation.cylinder(radius=r_out - rim_gap, height=z1 - z0 + 20,
                                      sections=140)
    band = trimesh.boolean.difference([outer, inner])
    band.apply_translation((0, -r_out, (z0 + z1) / 2))
    keep = trimesh.creation.box(extents=(2 * half_width, r_out, z1 - z0 + 6))
    keep.apply_translation((0, -r_out / 2, (z0 + z1) / 2))
    return trimesh.boolean.intersection([band, keep])


def shot_hero(rim_gap: float):
    """The device as it arrives: bay, lid, hook, sleeve and cap, on nothing."""
    parts = device_parts(rim_gap)
    eye, target = (330, 330, 150), (0, 0, -70)
    img = render(parts, eye=eye, target=target, size=(1260, 1200), ss=2,
                 shadow={"centre": (-4, -8), "radii": (56, 30), "strength": 0.14})
    return save(img, "hero.png")


def shot_exploded(rim_gap: float):
    explode = {
        "bay_lid": (64, -40, 0),
        "bay_gasket": (64, -48, 0),
        "probe_cap": (26, -52, -44),
        "probe_gasket": (26, -44, -38),
    }
    parts = device_parts(rim_gap, explode)
    eye, target = (-390, -320, 70), (10, -30, -86)
    img = render(parts, eye=eye, target=target, size=(1440, 1180), ss=2,
                 margin=0.06)
    items = [
        ("bay lid + gasket", (46, -44, -22), (0.80, 0.12)),
        ("M16 USB-C charge port", (ss.CHARGE_PORT_X + 4, 29, ss.CHARGE_PORT_Z),
         (0.03, 0.30)),
        ("body: bay, hook over the rim, leg", (-42, 16, 2), (0.02, 0.60)),
        ("probe sleeve", (-16, -20, -98), (0.74, 0.55)),
        ("probe cap + gasket", (26, -64, -150), (0.80, 0.90)),
    ]
    img = annotate(img, parts, eye, target, items, size=(1440, 1180), margin=0.06)
    return save(img, "exploded.png")


def shot_mounted(rim_gap: float):
    parts = device_parts(rim_gap) + pot_parts(rim_gap) + plant_parts()
    eye, target = (330, 300, 170), (0, -40, -66)
    img = render(parts, eye=eye, target=target, size=(1300, 1150), ss=2,
                 margin=0.05, shadow={"centre": (0, -70), "radii": (98, 98),
                                      "strength": 0.10})
    return save(img, "mounted.png")


def shot_room_view(rim_gap: float):
    """From the room, at eye level: the pot is all you see."""
    parts = device_parts(rim_gap) + pot_parts(rim_gap) + plant_parts()
    eye, target = (-60, -560, 14), (0, -60, -66)
    img = render(parts, eye=eye, target=target, size=(1300, 1050), ss=2,
                 margin=0.05)
    return save(img, "room_view.png")


def shot_views(rim_gap: float):
    parts = device_parts(rim_gap)
    size = (640, 880)
    front = render(parts, eye=(0, 900, -66), target=(0, 0, -68), size=size, ss=3,
                   margin=0.07)
    side = render(parts, eye=(900, 0, -60), target=(0, 0, -68), size=size, ss=3,
                  margin=0.07)
    back = render(parts, eye=(-40, -900, 120), target=(0, 0, -70), size=size, ss=3,
                  margin=0.07)
    return contact_sheet([front, side, back],
                         ["front - 88 mm wide, charge port",
                          "side - 57 mm deep, rim slot in profile",
                          "back - lid, screws, sleeve"],
                         "views.png")

def shot_plate(rim_gap: float, bed: float = 235.0):
    """The five parts on a build plate, already in their print orientations."""
    src = STL / "print"
    files = sorted(src.glob(f"*_rim{rim_gap:g}.stl"))
    if not files:
        raise SystemExit(f"no print STLs in {src} - run cad/orient.py first")
    parts = [(trimesh.load(p), PART_COLOURS[p.stem.rsplit("_", 1)[0]],
              p.stem.rsplit("_", 1)[0]) for p in files]

    gap = 12.0
    order = sorted(parts, key=lambda pc: (-pc[0].extents[1], -pc[0].extents[0]))
    rows, row, row_w = [], [], 0.0
    for mesh, colour, name in order:
        w, d = mesh.extents[0], mesh.extents[1]
        if row and row_w + gap + w > bed:
            rows.append((row, row_w))
            row, row_w = [], 0.0
        row.append((mesh, colour, name, w, d))
        row_w += (gap if row_w else 0.0) + w
    rows.append((row, row_w))

    total_d = sum(max(d for _, _, _, _, d in r) for r, _ in rows) + gap * (len(rows) - 1)
    y = -total_d / 2
    placed, labels = [], []
    for r, width in rows:
        depth = max(d for _, _, _, _, d in r)
        x = -width / 2
        for mesh, colour, name, w, d in r:
            m = mesh.copy()
            m.apply_translation((x + w / 2, y + depth / 2, 0.0))
            placed.append((m, colour))
            labels.append((f"{name.replace(chr(95), chr(32))}  "
                           f"{w:.0f} x {d:.0f} x {mesh.extents[2]:.1f} mm",
                           (x + w / 2, y + depth / 2, mesh.extents[2])))
            x += w + gap
        y += depth + gap

    # stagger the caption boxes into two columns so the text never stacks up
    base_mesh = trimesh.creation.box(extents=(bed, bed, 2.0))
    base_mesh.apply_translation((0, 0, -1.0))
    pre = [(base_mesh, (200, 202, 206))] + placed
    left = right = 0
    staggered = []
    for text, anchor in labels:
        px, _ = to_px(anchor, (300, -330, 430), (0, 0, 40), (1300, 1240), 0.05, pre)
        if px < 650:
            staggered.append((text, anchor, (0.02, 0.20 + 0.10 * left)))
            left += 1
        else:
            staggered.append((text, anchor, (0.63, 0.20 + 0.10 * right)))
            right += 1
    labels = staggered

    base = trimesh.creation.box(extents=(bed, bed, 2.0))
    base.apply_translation((0, 0, -1.0))
    scene = [(base, (200, 202, 206))] + placed
    eye, target = (300, -330, 430), (0, 0, 40)
    img = render(scene, eye=eye, target=target, size=(1300, 1240), ss=2,
                 margin=0.05, key_dir=(-0.40, 0.60, 0.69),
                 bg_top=(251, 251, 252), bg_bottom=(212, 215, 221))
    img = annotate(img, scene, eye, target, labels, size=(1300, 1240),
                   margin=0.05, font_px=22)
    return save(img, "print_plate.png")




def main():
    ap = argparse.ArgumentParser(description="SoilSitter preview renders")
    ap.add_argument("--rim-gap", type=float, default=ss.RIM_GAP)
    ap.add_argument("--only", default="", help="comma list: hero,exploded,mounted,room,views,plate")
    args = ap.parse_args()
    want = {p.strip() for p in args.only.split(",") if p.strip()}

    def run(key, fn):
        if not want or key in want:
            fn(args.rim_gap)

    run("hero", shot_hero)
    run("exploded", shot_exploded)
    run("mounted", shot_mounted)
    run("room", shot_room_view)
    run("views", shot_views)
    run("plate", shot_plate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
