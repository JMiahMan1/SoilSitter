# Changelog

## 1.0.1 — 2026-11-20

**Fixed: both gaskets were modelled floating in mid-air.** Rendering the parts
from different angles (rather than flat drawings) exposed it: the bay gasket sat 1.5
mm outside the lid and the probe gasket hung 11 mm away from the sleeve, in the gap
where the pot wall goes. Neither was visible in an assembled view, and neither would
have sealed anything on a printed part.

- `bay_gasket` now lies on the lid's inner face (Y 0–1 mm), inside the bay's 1 mm
  rebate, and is notched around the hook bridge.
- `probe_gasket` now lines the cavity mouth (Y −15…−14 mm), against the cap's inner
  face: radial compression in the seat, which is what a plug-type cap can actually
  do. It is a splash seal, not a face seal.
- `check_fit.py` gained four checks that assert each gasket touches the part it
  seals and fits inside it, so this cannot come back silently.

**Printability (asked, measured, then fixed)**

As exported, this was not an easy print, and the numbers say why:

- The body is 144.5 mm tall with its mass in the bay, so sleeve-down on the bed
  meant a 140 mm tower on a 32 × 13 mm foot *and* an 88 × 30 mm bay floor starting
  in mid-air. Turned over (bay down, sleeve up) the bed contact becomes 3685 mm²
  and the heavy end sits on the plate.
- The lid, cap and both gaskets were exported in assembly orientation, i.e. standing
  on a 1–2.5 mm edge. Unprintable on any machine; they are all flat now.
- The last 406 mm² of free overhang was the probe sleeve's flat 25 × 6 mm top face.
  It is roofed at 45° now (a 6.5 mm ridge), which takes the free overhang to
  **0 mm²** — all five parts print with no support at all.

- `cad/orient.py` scores all 24 axis-aligned orientations per part (free overhang,
  the height of that overhang, bed contact, slenderness), separating overhang that
  needs support from internal bridging that no support can reach, and writes
  `stl/print/` pre-rotated plus `manifest_rim<N>.json`. Measured for rim 9: body
  88 × 57 × 144.5 mm, 0 mm² support, 2832 mm² bridged.
- `check_fit.py` imports the same scoring and fails if a free overhang comes back.
- `docs/diagrams/print_plate.png`: all five parts on a 235 mm bed in their print
  orientations, rendered from the exported print STLs.
- `ASSEMBLY.md` says which units to slice (no support anywhere) and names the one
  real risk left: a 144.5 mm print that wants a brim and a slow first 40 mm on a
  bed-slinger. The height is set by the 98 mm probe PCB and cannot be reduced.

**Added**

- `cad/preview.py`: an orthographic z-buffer renderer with per-corner normals
  (smooth fillets, hard edges), camera-relative three-light shading, 2–3× super-
  sampling, studio background, contact shadow, ghosted-material pass and PIL
  leader-line labels. It produces the README gallery: `hero.png`, `exploded.png`,
  `mounted.png`, `room_view.png`, `views.png` (front/side/back).
- `render.py` is now only the X=0 cutaway (`section.png`); the photographic views
  moved to `preview.py`.

**Changed**

- `ASSEMBLY.md` describes where each gasket actually goes.
- The README gallery captions the room view honestly: the bay's top plate stands
  4.5 mm proud of the rim, so a sliver shows over it from the room. Hang the unit
  with that sliver behind the foliage.

## 1.0.0 — 2026-11-20


First release: a complete battery-powered soil-moisture sensor that hangs on a pot.

**Case** (`cad/soilsitter.py`, `stl/`)

- Body, bay lid, probe cap and two gaskets, parametric in pot rim thickness.
- Ships as `rim6`, `rim9` and `rim12` STL sets plus a manifest of volumes and
  bounding boxes per part.
- Bay on the outside of the pot with a 2.5 mm standoff, hook over the rim, leg
  down the inner wall, probe sleeve down to Z = −140 mm.
- Wire route: probe cavity → groove up the leg → tunnel over the rim → notch into
  the bay, sized for three 26 AWG silicone wires.
- M16 panel-mount USB-C charge port in the bay wall, hidden behind the pot.
- Four M2.5 self-tapping screws, Ø2.1 mm pilots, no inserts.
- `cad/check_fit.py` verifies watertightness, hardware packing and clearances,
  screw keep-outs, probe and connector fit, the sampled wire route, the rim slot,
  lid notch, cap coverage, overhang area and the bridge span — for every rim size.

**Firmware** (`firmware/soilsitter.yaml`)

- ESP32-C3 SuperMini on esp-idf, ESPHome 2026.9, compiled and validated.
- Deep sleep with a wake window, `KEEP_AWAKE` wake button on GPIO3, and a
  `provisioned` global so a factory-fresh node stays awake until the hub adopts it.
- Probe powered from GPIO5 only while measuring; 1 MΩ/1 MΩ battery divider.
- `sensor.soil_moisture` with `device_class: moisture` and a linear calibration,
  battery percentage, Wi-Fi signal, uptime, status, Stay Awake / Sleep Now /
  Restart / Safe Mode.
- Native API with Noise encryption, OTA guarded against deep sleep, fallback
  captive-portal AP.

**Docs**

- `docs/BOM.md` (Amazon, two units per order), `WIRING.md`, `ASSEMBLY.md`,
  `CALIBRATION.md`, `USAGE.md`, `INTEGRATION.md` (Home Hub adoption and the Garden
  moisture binding), plus a rendered hero, mounted and section diagram.

**Known limits**

- Designed against datasheet dimensions, not a physical build. The USB-C pigtail
  and the probe cap are the two fits most likely to need a tolerance tweak.
- Battery life is arithmetic, not a discharge test: ~4–6 months expected at a
  30-minute interval.
- The 12 mm variant needs support under the hook bridge (14.5 mm span).
- The Thingiverse original (thing 6908755) was unreachable when this was written
  (Cloudflare), so the hardware choices here are this project's own.
