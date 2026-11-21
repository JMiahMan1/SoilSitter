# Bill of materials

Everything here is US Amazon stock, chosen so that **one order builds two
SoilSitters**. Prices are the listing prices in November 2026 and will drift;
where a specific listing matters (the parts whose dimensions the case is cut for)
I link the product page, otherwise I link a search because those listings rotate
weekly.

**Total: about $55** for two complete units (~$22 each), or ~$35 if you already
own wire, resistors and screws.

## The parts that define the case

| # | Part | Spec the case depends on | Qty | ~Price | Link |
|---|---|---|---|---|---|
| 1 | **ESP32-C3 SuperMini** | 22.52 × 18 mm board, 2.54 mm pitch, USB-C, buttons on the long edges — check **GPIO3** is on the header | 3 | $16 | [Teyleten Robot 3-pack](https://www.amazon.com/dp/B0D47G24W3) |
| 2 | **Capacitive Soil Moisture Sensor V1.2** | 98 × 23 × 1.6 mm PCB (listing states 23 × 98), sensing face on the back, connector at the cable end — **must be ≤ 6.6 mm tall** (JST-PH socket yes, straight 2.54 mm header no) | 2 | $9 | [Gikfun 2-pack](https://www.amazon.com/dp/B07H3P1NRM) |
| 3 | **TP4056 Type-C charge module** | **Type-C**, DW01 + dual-MOSFET protection, **≤ 17.5 × 29 × 4.5 mm overall** (the shell counts, not just the 26 × 17 board) | 5 | $8 | [search: TP4056 Type-C with protection](https://www.amazon.com/s?k=tp4056+type-c+with+protection+module) |
| 4 | **103450 LiPo, 3.7 V 2000 mAh** | 10 × 34 × 50 mm nominal, 10.5 × 35 × 52 mm as built (protection PCB + sleeve + leads) | 2 | $18 | [search: 103450 2000 mAh JST](https://www.amazon.com/s?k=103450+3.7v+2000mah+lipo+battery+jst) |
| 5 | **M16 USB-C panel-mount pigtail** | 16 mm thread, 20 mm hex nut, ≤ 13 mm of body behind the panel — a 90° plug is easiest | 2 | $10 | [search: M16 USB-C panel mount](https://www.amazon.com/s?k=M16+USB-C+panel+mount+extension+cable) |

Every number in that table is checked against the case by `cad/check_fit.py`, and
[FIT.md](FIT.md) lists the published size, the source, and the clearance the case
gives each part.

Notes on each:

1. **ESP32-C3 SuperMini.** Any C3 SuperMini clone works. Avoid the C3/C6 boards
   that are 26 mm wide — they do not fit the 22.5 mm bay channel. Many clones ship
   with a bright red power LED that costs ~1 mA continuously; see
   [USAGE.md](USAGE.md#the-power-led) for removing it (roughly doubles
   run time) or leave it and accept ~3 months.
2. **Sensor V1.2, not V1.0, not "V2.0", not resistive.** V1.2 is the 555-timer
   board with a 3–5 year electrode life and a 0.3–3.0 V output. The Gikfun 2-pack
   (EK1940) is this board: its listing gives 0.91 × 0.01 × 3.86 in, i.e. **23 × 98
   mm** — the size the case is cut for. The longer "V2.0" boards will not fit.
   **Check the connector before you wire it.** The sleeve leaves 6.6 mm above the
   PCB: a JST-PH 2.0 socket (5.6 mm) fits and its supplied cable climbs the 1.5 mm
   channel behind it, so nothing is soldered at the probe. A **straight 2.54 mm
   header is ~8.5 mm and will not close under the cap** — desolder it and solder
   wires to the pads, or fit a right-angle header.
3. **TP4056 with protection, and Type-C.** The bare TP4056 boards without the
   DW01 + dual MOSFET will over-discharge a pouch cell. It also has to be the
   **Type-C** version: the panel pigtail is USB-C, and a micro-USB board will not
   accept it. This used to link a specific 10-pack (ASIN B07PKND8K9); that page
   returned 404 in November 2026, so it is a search link now. Measure the module
   across its longest axis before you commit: 26 × 17 mm is the PCB, 29 mm is the
   part, and the case is cut for 29.2 mm.
4. **Battery.** 103450 = 10 × 34 × 50 mm, 2000 mAh nominal. Check the listing's
   dimensions rather than the model number: with its protection PCB and sleeve a
   cell usually measures 10.5 × 35 × 52 mm. That is what the bay is sized for —
   53 mm of clear height, i.e. 0.5 mm at each end. It is the tightest fit in the
   case, and the one to measure with calipers before you print. Cells ship
   ground-only; expect a week.
5. **USB-C pigtail.** The bay wall has a Ø16.2 mm hole for an M16 threaded panel
   connector, and the bay gives the nut (20 mm across flats) 1.0 mm of clearance
   at the side wall plus **13 mm of body** behind the panel before it reaches the
   battery. A straight pigtail with a long overmould will not fit; a 90° plug, or
   a straight one whose cable turns immediately, will. This is the charge port;
   the pigtail's own cap keeps splash out.


## Electronics passives

| # | Part | Qty | ~Price | Link |
|---|---|---|---|---|
| 6 | **HT7333-A 3.3 V LDO**, SOT-89 (battery rail → C3 `3V3`) | 5 | $8 | [search: HT7333 LDO](https://www.amazon.com/s?k=ht7333+3.3v+ldo) |
| 7 | 1 MΩ resistors, 1/4 W (battery divider) | 2 | $6 / kit | [search: 1M ohm resistor kit](https://www.amazon.com/s?k=1m+ohm+resistor+1%2F4w+assortment) |
| 8 | 100 nF + 10 µF capacitors (ADC filter, rail) | 4 | $7 / kit | [search: capacitor assortment](https://www.amazon.com/s?k=ceramic+capacitor+assortment+kit) |
| 9 | 26 AWG silicone hookup wire, 4 colours | 1 kit | $12 | [search: 26 awg silicone wire kit](https://www.amazon.com/s?k=26+awg+silicone+wire+kit) |
| 10 | JST-PH 2.0 pigtails (only if your probe has bare pads or a 2.54 mm header) | 1 set | $7 | [search: JST-PH 2.0 cable](https://www.amazon.com/s?k=jst-ph+2.0+3+pin+cable) |

The LDO is not optional: a 3.7 V cell cannot feed the C3's 5 V pin (its regulator
needs ~4.5 V in) and putting 4.2 V straight on `3V3` is out of spec. The HT7333
drops out at 3.4 V in, so you get the full cell range, and it sips 4 µA in
quiescent. You need two resistors and three capacitors; an assortment is cheaper
than buying singles and you will use the rest. Silicone wire matters: the
probe leg bends every time the sensor comes out of the pot, and PVC insulation
work-hardens and cracks.

## Mechanical

| # | Part | Qty | ~Price | Link |
|---|---|---|---|---|
| 11 | M2.5 × 10 mm pan-head self-tapping screws | 4 | $9 / kit | [search: M2.5 self-tapping 10 mm](https://www.amazon.com/s?k=m2.5+self+tapping+screws+10mm+pan+head) |
| 12 | 1 mm silicone sheet, 100 × 100 mm (gaskets) | 1 | $8 | [search: 1mm silicone sheet](https://www.amazon.com/s?k=1mm+silicone+sheet+food+grade) |
| 13 | 3 mm adhesive foam tape (battery pad) | 1 | $7 | [search: 3mm foam tape](https://www.amazon.com/s?k=3mm+thick+double+sided+foam+tape) |

The screws are **self-tapping into printed Ø2.1 mm pilots** — no heat-set inserts,
no nuts. Two go into the bay's top wall, two into the bottom corner bosses. If you
plan to open the case often, run an M2.5 tap through the pilots once; either way
they survive about ten insertions.

The gaskets print in TPU if you have it (the STLs are 1 mm thick), or cut them
from the silicone sheet using the printed gasket as a template. Optional for a
windowsill plant, worth it for a bathroom fern.

## Tools

| Tool | Why |
|---|---|
| Soldering iron, fine tip, 350 °C | TP4056 pads and the probe header are small |
| Flux pen + 0.6 mm solder | Flux is not optional on factory-tinned pads |
| Multimeter | Continuity before power, divider ratio, battery voltage |
| Flush cutters + strippers down to 30 AWG | 26 AWG is easy; the probe's leads are not |
| USB-C **data** cable | Charge-only cables cannot flash, and this trips people up |
| Small needle-nose pliers | Seating the probe connector inside the sleeve |
| Calipers | Measuring your pot rim — the one measurement that matters |
| Digital scale (optional) | Confirms the print is solid, not 40 % air |

## Substitutions

- **LiFePO4 14500 instead of LiPo**: 3.2 V works (the C3 runs down to 3.0 V), but
  the TP4056 cannot charge it — you need a 3.6 V CC/CV charger, and the battery
  curve in the firmware has to change.
- **18650 in a holder**: does not fit. The design is deliberately built around a
  flat pouch cell so the case stays under 30 mm deep.
- **BME280 instead of the soil probe**: fits the same sleeve (cavity is
  25 × 7 mm) and gives temperature and humidity, but then it is not a soil sensor.
- **Charge through the C3's own USB-C and skip the pigtail**: you lose the
  weatherproof charge port and have to remove the lid every time. Fine on a desk,
  annoying on a shelf.
