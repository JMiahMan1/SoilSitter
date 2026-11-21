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
| 1 | **ESP32-C3 SuperMini** | 22.5 × 18 mm board, USB-C on the short edge, buttons on the long edges | 3 | $16 | [Teyleten Robot 3-pack](https://www.amazon.com/dp/B0D47G24W3) |
| 2 | **Capacitive Soil Moisture Sensor V1.2** | 98 × 23 × 1.6 mm PCB, 3-pin header at one end, sensing face on the back | 2 | $9 | [Gikfun 2-pack](https://www.amazon.com/dp/B07H3P1NRM) |
| 3 | **TP4056 Type-C charge module** | 26 × 17 mm board with DW01 protection, 2 mounting pads | 10 | $9 | [10-pack, Type-C + protection](https://www.amazon.com/dp/B07PKND8K9) |
| 4 | **103450 LiPo, 3.7 V 2000 mAh** | 10 × 34 × 50 mm pouch with 2-pin JST | 2 | $18 | [search: 103450 2000 mAh JST](https://www.amazon.com/s?k=103450+3.7v+2000mah+lipo+battery+jst) |
| 5 | **M16 USB-C panel-mount pigtail** | 16 mm thread, ≤ 30 mm behind the panel, 90° is easiest | 2 | $10 | [search: M16 USB-C panel mount](https://www.amazon.com/s?k=M16+USB-C+panel+mount+extension+cable) |

Notes on each:

1. **ESP32-C3 SuperMini.** Any C3 SuperMini clone works. Avoid the C3/C6 boards
   that are 26 mm wide — they do not fit the 22.5 mm bay channel. Many clones ship
   with a bright red power LED that costs ~1 mA continuously; see
   [docs/USAGE.md](docs/USAGE.md#the-power-led) for removing it (roughly doubles
   run time) or leave it and accept ~3 months.
2. **Sensor V1.2, not V1.0, not "V2.0", not resistive.** V1.2 is the 555-timer
   board with a 3–5 year electrode life and a 0.3–3.0 V output. The case is cut
   for the 98 × 23 mm V1.2; the longer "V2.0" boards will not fit.
3. **TP4056 with protection.** The bare TP4056 boards without the DW01 + dual
   MOSFET will over-discharge a pouch cell. The 10-pack is cheaper than a
   protected 2-pack and gives you spares for other projects.
4. **Battery.** 103450 = 10 × 34 × 50 mm, 2000 mAh nominal. Check the listing's
   dimensions rather than the model number: sellers sometimes ship 103450 cells
   that measure 10 × 34 × 52 mm, which still fits (the bay has 54 mm clear) but is
   tight. Cells ship ground-only; expect a week.
5. **USB-C pigtail.** The bay wall has a Ø16.2 mm hole for an M16 threaded panel
   connector. The plug needs **≤ 30 mm** behind the panel or it collides with the
   battery. This is the charge port; the pigtail's own cap keeps splash out.


## Electronics passives

| # | Part | Qty | ~Price | Link |
|---|---|---|---|---|
| 6 | **HT7333-A 3.3 V LDO**, SOT-89 (battery rail → C3 `3V3`) | 5 | $8 | [search: HT7333 LDO](https://www.amazon.com/s?k=ht7333+3.3v+ldo) |
| 7 | 1 MΩ resistors, 1/4 W (battery divider) | 2 | $6 / kit | [search: 1M ohm resistor kit](https://www.amazon.com/s?k=1m+ohm+resistor+1%2F4w+assortment) |
| 8 | 100 nF + 10 µF capacitors (ADC filter, rail) | 4 | $7 / kit | [search: capacitor assortment](https://www.amazon.com/s?k=ceramic+capacitor+assortment+kit) |
| 9 | 26 AWG silicone hookup wire, 4 colours | 1 kit | $12 | [search: 26 awg silicone wire kit](https://www.amazon.com/s?k=26+awg+silicone+wire+kit) |
| 10 | JST-XH 3-pin cable (probe connector, optional) | 1 set | $7 | [search: JST-XH 3 pin cable](https://www.amazon.com/s?k=jst-xh+3+pin+cable) |

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
