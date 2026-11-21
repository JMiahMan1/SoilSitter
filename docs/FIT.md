# Does the real hardware fit?

The case is not cut to guesses. Every cavity in `cad/soilsitter.py` is sized from
a **published dimension** for the part in the BOM, and `cad/check_fit.py` asserts
that the part, as a solid box in its mounted position, clears the printed walls
and every other part. If a part changes size, the build fails — it does not
silently print a case that traps it.

Run it yourself:

```bash
python cad/check_fit.py --rim 6     # also 9 and 12
```

## The measurement sheet

| Part | Published size (mm) | Source | Case allowance | Clearance |
|---|---|---|---|---|
| ESP32-C3 SuperMini | **22.52 × 18**, 1.6 PCB + 3.2 USB-C, 2.54 pitch | [espboards.dev](https://www.espboards.dev/esp32/esp32-c3-super-mini/) — they measure it, quote 22.52 × 18, and link the GrabCAD model | open bay, 4.8 mm deep on the lid (no printed channel) | **3.0 mm** to the sides |
| TP4056 Type-C module | **17.3 × 29 × 4.3** overall (26 × 17 board + 3 mm Type-C shell) | [Xem Studio measured outline](https://xemstudio.com/) — free STEP/STL, CC BY 4.0; [sigmanortec](https://sigmanortec.ro/en/lithium-battery-charging-module-tp4056-typec-5v-1a-with-protection) gives 26 × 17 for the bare board | 29.2 × 17 × 4.3 pocket next to the C3 | **4.0 mm** to the sides |
| Capacitive soil V1.2 | **98 × 23 × 1.6** PCB, JST-PH 2.0 socket 5.6 mm tall, 20 cm cable | [makerselectronics](https://makerselectronics.com/product/capacitive-soil-moisture-sensor-v1-2) ("98 x 23mm", JST PH2.0, 20 cm cable); [tinkered.ai](https://www.tinkered.ai/components/capacitive-soil-moisture-v12) (SEN0193 clone, 3.3–5.5 V, 5 mA) | 25 × 8.9 × 106 cavity | **2.0 mm** across, **1.5 mm** behind the socket for the cable |
| 103450 LiPo | 10 × 34 × 50 nominal, **10.5 × 35 × 52** as built | cell naming convention + protection PCB/sleeve/leads | 27 × 10.5 × 53 pocket | **0.5 mm** at each end — the tightest fit in the case |
| M16 USB-C pigtail | 16 mm thread, 20 mm hex nut, ~13 mm body behind the panel | M16 panel-mount standard (thread M16 × 1.0) | Ø16.2 hole in the 3 mm wall, nut pocket | **1.0 mm** at the side wall, 13 mm of depth |
| HT7333 LDO | **4.5 × 4.0 × 1.5**, SOT-89 | datasheet package drawing | sits beside the charger on the lid | **18.5 mm** |

Two numbers deserve a comment.

**The TP4056 is 29 mm, not 26.** The bare board is 26 × 17, which is what most
listings quote, but the Type-C shell hangs 3 mm past the PCB edge — the thing
actually measures 17.3 × 29 × 4.3. Version 1.0.1 of this case was checked against
25 × 19, so the shell would have pressed into the screw boss. It is now cut for
the real outline. If you buy a *micro*-USB TP4056 instead, it is ~2 mm shorter and
still fits.

**The probe's connector is 6.6 mm or nothing.** The cavity leaves 6.6 mm above the
PCB before the cap's inner face. A JST-PH 2.0 socket is 5.6 mm and fits, with
1.5 mm behind it for its cable to climb into the wire pocket — on boards that
ship that way, the probe end is a factory crimp and nothing is soldered at the
probe. A **straight 2.54 mm header stands ~8.5 mm and the cap will not close**, so
those boards need the header desoldered (wires straight to the pads) or replaced
with a right-angle one. This is the difference between a 30-second fit and a
build that stops at the last step.

## Do these match the Amazon listings?

The models above are for the *part family*. Whether they match the exact ASIN in
the BOM is a separate question, so here is what each listing actually says, checked
on 2026-11-20:

| BOM item | Listing status | What the listing says | Verdict |
|---|---|---|---|
| Sensor — Gikfun EK1940, `B07H3P1NRM` | live, 2-pack | Item dimensions **0.91 × 0.01 × 3.86 in = 23 × 98 mm** | **Matches.** The 0.01 in thickness field is junk (the PCB is 1.6 mm); length and width are the case's numbers to a tenth of a mm. No cable is mentioned in the title — check the connector on the board you receive. |
| C3 — Teyleten Robot, `B0D47G24W3` | live, 3-pack | No dimensions, no pinout, no headers listed | **Unverified from the listing.** The model is the SuperMini standard (22.52 × 18). Since the bay is an open cavity and not a printed channel, a board 1 mm longer or 2 mm wider still fits — but confirm **GPIO3** is broken out, because the firmware wakes on it. |
| Charger — `B07PKND8K9` | **404, dead** | — | **Could not verify, and the link was broken.** BOM now points at a search with the constraints written down: Type-C, DW01 + MOSFET protection, ≤ 17.5 × 29 × 4.5 mm overall. |
| Cell | search link, no fixed ASIN | — | No listing to match. This is why the cell is the one part to measure with calipers. |
| Pigtail | search link, no fixed ASIN | — | Same. The constraint is ≤ 13 mm of body behind the panel. |

So: the probe's model matches its listing's own stated size; the C3's model is
standard-family, not listing-verified; the charger's link is dead and now a search.
Those three answers are different, and they are the honest ones.

## 3D models of the parts

If you want to check the fit yourself before printing, these are real models
rather than approximations:

- **ESP32-C3 SuperMini** — [GrabCAD library entry](https://grabcad.com/library/esp32-c3-supermini-1)
  (linked from espboards.dev), plus a [Printables model](https://www.printables.com/model/1360390).
- **TP4056 USB-C charger module** — STEP **and** STL free from
  [Xem Studio](https://xemstudio.com/) at the measured 17.3 × 29 × 4.3 mm.
- **Capacitive soil moisture sensor V1.2** — [GrabCAD](https://grabcad.com/library/capacitive-soil-moisture-sensor-v1-2-2);
  a dozen Printables cases model the same 98 × 23 board.
- **103450 cell** — no model needed: it is a rounded box, and that is how it is
  treated here (10.5 × 35 × 52).

Load any of them into the same scene as `stl/print/body_rim9.stl` and you will see
the same clearances the check reports.

## What to measure before you print

Three numbers, with calipers, on the parts you actually received:

1. **Cell length** (the 52 mm axis). Over 52.5 mm → shorten the battery pocket
   with a knife, or print the rim 12 body which has the same bay.
2. **Charger length** (the 29 mm axis). Some batches use a shorter micro-USB
   board (26–27 mm), which leaves more room.
3. **Probe width.** 23 mm is standard; a 24 mm board still fits the 25 mm cavity
   but loses the 1 mm per side that keeps the sensing face flat against the wall.

Anything outside those tolerances is a listing substitution, not a design
tolerance — check the listing before ordering.

## Honest limits

- The C3's board outline (22.52 × 18) is published; its USB-C shell height
  (3.2 mm) is a common-parts figure, not this listing's drawing. The 4.8 mm
  allowance covers it with 0.2 mm to spare, and the board is taped, not clamped.
- Clone variance is real: C3 SuperMini boards range 22.0–22.8 mm long, and
  "103450" cells range 50–53 mm. The clearances above are what the case gives at
  the published size.
- **The probe connector is the one real interference risk.** The sleeve leaves
  6.6 mm above the PCB. JST-PH sockets fit; a straight 2.54 mm header (~8.5 mm)
  does not, and neither does a board with a soldered Dupont wire bundle standing
  up. `check_fit.py` prints the 6.6 mm envelope as a NOTE rather than a PASS,
  because it depends on what your board shipped with.
- Nothing here has been printed or assembled yet. The fit is arithmetic plus
  meshes, not a build log — the first physical build is still the real test.
