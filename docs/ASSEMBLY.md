# Assembly

Three printed parts, two gaskets, four screws. About 45 minutes of assembly once
the print is off the bed, most of it waiting for silicone to cure.

## Print settings

| | |
|---|---|
| Material | PETG or ASA outdoors; PLA is fine indoors but creeps under the bay's screw load in a hot window |
| Layer | 0.20 mm (0.28 mm is acceptable, 0.16 mm for the lid's sealing face) |
| Walls | 3 perimeters, 4 on the body |
| Infill | 15 % gyroid |
| Supports | **Build-plate only**, under the rear of the bay floor |
| Brim | 8 mm on the body |
| Orientation | As exported: probe sleeve down, bay up |

Supports are needed in exactly one place: the bay's floor is an 88 × 30 mm plate
that starts in mid-air. Because the supported face is the **underside of the bay**,
the scars end up hidden against the pot. `cad/check_fit.py`'s overhang analysis
puts the unsupported area at ~2300 mm² centred on Z ≈ −58 mm, Y ≈ 13–31 mm —
that is the region to make sure your slicer paints. The rim hook bridges its
11 mm slot on its own and does not need support.

Expect **~50 g** of filament for the body and **~8 h** on a 0.4 mm nozzle at
0.20 mm layers. The lid and cap are 25 minutes each.

| Part | Print notes |
|---|---|
| `body` | Sleeve down. The 140 mm tall sleeve is a thin tower: brim is not optional. Check that the wire groove up the leg is clear with a 5 mm hex key before you assemble |
| `body_rim12` | Adds one thing: support under the hook bridge, where the 12 mm rim leaves a 14.5 mm span. `check_fit --rim-gap 12` prints a NOTE instead of a pass for that reason |
| `bay_lid` | Print flat, outside face down. The bottom lip is a 1 mm feature — if your first layer squashes badly, the lip will not hook under the body; print it at 0.16 mm |
| `probe_cap` | Flat, gasket groove up |
| `bay_gasket` | TPU at 0.20 mm, or cut from 1 mm silicone sheet using the STL as a template |
| `probe_gasket` | Same |

## Fasteners

Four M2.5 × 10 mm self-tapping screws, straight into printed Ø2.1 mm pilots:

- two into the bay's top wall (Z ≈ +2 mm),
- two into the bottom corner bosses (Z ≈ −41 mm).

Run each screw in **once, slowly, then back it out** before final assembly. That
cuts the thread and burnishes the hole; doing it with the gasket in place tends to
skew the screw and strip the pilot. If a pilot strips, a drop of CA glue and three
minutes will hold it for another cycle.

## Step by step

1. **Test the electronics outside the case.** Flash the firmware, confirm Wi-Fi and
   a soil reading on the bench ([CALIBRATION.md](CALIBRATION.md)). Debugging is
   much easier before the probe is down a sleeve.
2. **Clean the body.** Deburr the rim slot, the bay notch and the leg groove. Blow
   out the probe cavity; a stray string of PETG will stop the probe seating.
3. **Dry-fit the probe.** Slide the V1.2 board into the sleeve from the bottom,
   sensing face towards the 1.6 mm front wall. It should go in with light thumb
   pressure and stop against the collar at Z ≈ −30 mm. If it binds, the cavity
   floor has a blob — file it, do not force the board, the electrode is a thin
   copper pour and it will crease.
4. **Seat the C3 in the bay.** USB-C end towards the charge-port hole, antenna
   away from the battery. Two dabs of hot glue on the board's edge, not under it.
5. **Battery.** Foam tape on the back of the pouch, then press it into the bay
   floor with the leads towards the charge board. The cell must not sit on the
   TP4056 — that board gets warm while charging.
6. **Charge board and LDO.** Double-sided tape or a drop of hot glue, USB-C socket
   aligned with the panel pigtail. Plug the pigtail into it *before* you glue:
   the connector is easier to seat with the board loose.
7. **Dress the wiring.** The probe bundle goes up the leg groove and into the bay
   through the notch at the top; leave 30 mm of slack inside the bay so the lid
   closes without trapping a wire.
8. **Gaskets and lid.** Gasket onto the lid's groove, lip under the body's bottom
   edge, hinge the lid up, four screws finger-tight then a quarter turn. Do not
   overtighten: the gasket only needs to be compressed, and the pilot is plastic.
9. **Probe cap.** Gasket into the cap groove, cap over the sleeve's bottom lip,
   press until it clicks past the lip. It is trapped top and bottom, no screws.
   If you want it removable, a 20 mm strip of kapton tape across the seam is
   enough indoors.
10. **Hang it.** Slide the hook over the rim from the outside, leg first, probe
    down the inner wall. The bay should sit against the pot with 2.5 mm of standoff
    and the probe should be ~20 mm above the pot's floor — push it down until the
    hook's underside touches the rim.

## Mounting checks

- **Pot rim 6–12 mm?** Use the matching STL. The hook is a 1 mm-per-side fit; a
  10 mm rim in the 12 mm hook leans 2 mm, which is fine.
- **Tapered or rolled rims** (terracotta is usually rolled): measure at the point
  the hook will sit, not at the widest part.
- **Fabric pots** do not work — there is nothing rigid to hang on.
- **Probe depth** matters more than pot size: the V1.2 senses about 20 mm around
  its lower third, so the sleeve's bottom 60 mm should be in soil, not in the
  drainage layer. In a shallow pot, hang the unit so the sleeve's tip is 15 mm
  above the bottom.

## If the print fights you

| Problem | Fix |
|---|---|
| Screws strip the pilots | Print at 0.16 mm, or run an M2.5 tap; a 3 mm drop of CA in the hole sets hard in 5 min |
| Lid will not seat | The bottom lip is hanging on the body's fillet — chamfer the lip with a knife |
| Probe will not enter the sleeve | Stringing in the cavity; ream with a 6 mm drill bit **by hand** |
| Bay rocks on the pot | The rim is thicker than the hook; reprint at the next size up |
| Cap pops off when wet | The gasket is too thick (over 1.2 mm) and the lip cannot engage; sand the gasket to 0.8 mm |

Next: [CALIBRATION.md](CALIBRATION.md) so the percentages mean something.
