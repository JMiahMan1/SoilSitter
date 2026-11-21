# Changelog

## 1.0.4 — 2026-11-20

**Diagrams and assembly instructions brought in line with the measured hardware.**

The photographic renders were never wrong — they draw only the five printed parts —
but the technical drawing was, and nothing showed the inside of the bay, which is
what half of ASSEMBLY talks about.

- **New `docs/diagrams/bay_layout.png`**: plan view into the open bay with the lid
  off, showing where the SuperMini, TP4056, LDO, 103450 cell and M16 pigtail go,
  each labelled with its X/Z band *and* its Y depth. Solid parts are taped to the
  lid; hatched parts sit deeper. It is generated from the same `HARDWARE` boxes
  `check_fit.py` verifies, so the drawing cannot drift from the check.
- **`cad/render.py` would have crashed** on the new hardware names: the colour map
  used `next(...)` over name prefixes and had no entry for `ht7333`, and the label
  dict was indexed with `labels[name]` for names that no longer existed. It now
  uses explicit maps with lookups that tolerate new parts.
- `section.png` regenerated with the corrected boxes; the two leader lines that
  crossed the whole figure (soil line, pot wall) were moved out of the way.
- **`preview.py` had a dead `hardware_parts()`** that no scene called — 17 lines of
  a second, silently-drifting source of part sizes. Removed; `render.py` is the one
  place that draws hardware.
- **ASSEMBLY.md** now opens its build steps with a "What goes where" table (X, Z,
  depth, notes per part) that matches the drawing, and the steps were corrected:
  the cell stands on the floor against the **back wall** with its leads out of the
  top (it was "press it into the bay floor"), the LDO has a stated home between the
  two boards, the C3's antenna end is specified, and step 3 now checks the 6.6 mm
  connector envelope *before* the probe goes into the sleeve rather than after.
- README gallery and repo tree updated; `cad/preview.py`/`render.py` description
  corrected to say render.py draws two figures now.

All six photographic views re-rendered from the current STLs, `check_fit` passes
for rims 6/9/12, `esphome config` valid.


**Checked the models against the actual Amazon listings.** 1.0.2 measured the parts;
this checks whether those measurements describe the ASINs the BOM links. Answer:
one matches, one is unverifiable, one link is dead, and one of my own claims was
wrong.

- **Sensor (Gikfun `B07H3P1NRM`) matches.** The listing gives 0.91 × 0.01 × 3.86 in
  = **23 × 98 mm**, which is the case's number to a tenth of a millimetre. (The
  0.01 in thickness field is junk; the PCB is 1.6 mm.)
- **Charger (`B07PKND8K9`) is a dead link.** The page returns 404, so Type-C
  versus micro-USB could not be confirmed at all — and the panel pigtail is
  USB-C, so that distinction decides whether the unit can charge. The BOM now
  links a search with the constraints written out: Type-C, DW01 + MOSFET,
  ≤ 17.5 × 29 × 4.5 mm overall.
- **C3 (Teyleten Robot `B0D47G24W3`) is listed without dimensions or pinout.**
  The model is the SuperMini family standard (22.52 × 18). Because the bay is an
  open cavity and not a printed channel, ±1 mm is harmless — but the listing
  cannot confirm GPIO3 is broken out, and the firmware wakes on GPIO3, so that is
  now a build check rather than an assumption.
- **My "the probe needs no soldering" claim was wrong for this 2-pack.** The
  Gikfun listing sells bare boards, and the real constraint is the 6.6 mm of
  envelope above the PCB that the sleeve leaves before the cap's inner face. A
  JST-PH socket (5.6 mm) fits; a **straight 2.54 mm header is ~8.5 mm and the cap
  will not close** — those boards need the header off, or a right-angle one.
  WIRING, BOM and FIT now say so, and `check_fit.py` prints the 6.6 mm envelope as
  a NOTE (it depends on what shipped, so it cannot be a PASS/FAIL).

New `docs/FIT.md` section, "Do these match the Amazon listings?", records all of
the above with the listing status of each ASIN, so the next person does not have
to re-derive which numbers are verified and which are family-standard.


**Checked the case against the real parts instead of against my own guesses.**
`check_fit.py` had been validating hardware boxes I had estimated from memory. I
looked up published dimensions and measured outlines for all six parts, and two
of them were wrong.

- **The TP4056 is 29 mm long, not 26.** The bare board is 26 × 17 mm, but the
  Type-C shell hangs 3 mm past the PCB edge: the real footprint is 17.3 × 29 ×
  4.3 mm ([Xem Studio's measured outline](https://xemstudio.com/) ships STEP and
  STL). The pocket was cut 25 mm wide — the shell would have rested against the
  lid screw boss's 1.5 mm gap, and a slightly longer clone would have jammed. The
  pocket is now 29.2 × 17 × 4.3 and clears the boss by 0.8 mm.
- **The battery was quoted as fitting with 54 mm of room; the bay has 53.** A
  103450 cell with its protection PCB and sleeve measures 10.5 × 35 × 52 mm, so
  it fits with 0.5 mm at each end — it is the tightest part in the case, and BOM
  and FIT now say so instead of implying slack.
- **The USB-C pigtail allowance was 30 mm of body behind the panel; the bay gives
  13.** Corrected in the BOM, with the 20 mm nut pocket called out too.
- **The probe is not soldered at all.** The V1.2 ships with a 20 cm cable already
  crimped into a JST-PH socket, so WIRING now says to cut the Dupont ends and
  leave the probe end as a factory crimp — a better joint than a hand-soldered
  header in wet soil. The cavity already gave the socket 5.6 mm and a 1.5 mm
  cable channel behind it, which is now asserted.
- **New [docs/FIT.md](docs/FIT.md)**: every part's published size, its source,
  the allowance the case gives it, the clearance, 3D-model links, and what to
  measure with calipers before printing.

**`check_fit.py` changes**

- Hardware boxes now carry the source of each dimension in a comment, and the
  sensor is three boxes (PCB, SMD parts, JST socket) rather than one lump, so the
  cable channel is a real test.
- Board pockets sit flush with the bay's mouth because they are taped to the lid;
  the check now requires 0.4 mm on the sides and back but allows 0 at that face,
  and reports the number either way instead of failing on a correct design.
- New assertions: the JST socket leaves ≥1.2 mm behind it for the cable, and the
  probe PCB's side clearance is printed rather than assumed.

Geometry is unchanged: every part already fit the printed cavities. What changed
is that the numbers now mean something.


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
