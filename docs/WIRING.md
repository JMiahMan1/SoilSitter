# Wiring

Seven connections, all on the ESP32-C3 SuperMini's own header. Nothing is
level-shifted, nothing is on a bus, and every pin is a plain GPIO.

## Pin map

| Signal | C3 pin | Firmware | Notes |
|---|---|---|---|
| Probe power | `GPIO5` | `output: soil_power` | 3.3 V only while measuring (~5 mA) |
| Probe analogue out | `GPIO0` | `sensor: soil_voltage` (ADC1_CH0) | 0.3–3.0 V, 12 dB attenuation |
| Battery sense | `GPIO1` | `sensor: battery_voltage` (ADC1_CH1) | 1 MΩ / 1 MΩ divider, ×2 in firmware |
| Wake button (optional) | `GPIO3` | `deep_sleep: wakeup_pin` | Pull to GND to wake; GPIO3 is RTC-capable, the BOOT button (GPIO9) is not |
| 3.3 V in | `3V3` | — | From the LDO, **not** the 5 V pin |
| Ground | `GND` | — | Common for probe, divider, LDO |

Pins deliberately avoided: `GPIO8` (onboard LED), `GPIO9` (BOOT strapping),
`GPIO2` (strapping), `GPIO18/19` (USB). GPIO4, GPIO6, GPIO7, GPIO10, GPIO20 and
GPIO21 are free if you want a second probe later.

## Schematic

```
   103450 LiPo                 TP4056 (Type-C)              HT7333 LDO
  ┌───────────┐              ┌────────────────┐          ┌───────────┐
  │  B+ ──────┼──────────────┤ B+             │          │           │
  │  B- ──────┼──────────────┤ B-   OUT+ ─────┼──────────┤ IN    OUT ├── 3V3 ──┐
  └───────────┘              │      OUT- ─────┼──────┬───┤ GND       │         │
                             │  USB-C ◄── charge    │   └───────────┘         │
                             └────────────────┘      │                     ┌───┴────────────┐
                                                     │                     │  ESP32-C3      │
                             ┌── 1 MΩ ──┬───────────┴──(cell node)        │  SuperMini     │
                             │          │                                   │  3V3  ◄────────┤
   GPIO1 ◄───────────────────┤          │                                   │  GND  ─────────┤
                             └── 1 MΩ ──┴── GND                             │                │
                                   │                                        │  GPIO5 ──► probe VCC
                                 100 nF ── GND                              │  GPIO0 ◄── probe AOUT
                                                                            │  GND   ──► probe GND
   probe GND ─────────────────────────────────────────────────────────────► │  GPIO3 ──► button ── GND
                                                                            └────────────────┘
```

The divider sits on the **cell node** (TP4056 `OUT+`), not on the LDO output, so
the percentage tracks the battery rather than a rock-steady 3.3 V. It draws 2 µA
at 4.2 V — nothing next to the 4 µA quiescent of the HT7333.

## Wire runs and lengths

Cut silicone wire, tin the ends, and do not shorten the probe's own leads: its
3-pin header is easier to solder to a pigtail than to replace.

| Run | From → to | Length | Wire |
|---|---|---|---|
| A | Probe header → top of the probe cavity | 40 mm | 3 × 26 AWG |
| B | Probe cavity → up the leg groove → over the rim → bay notch | 210 mm | 3 × 26 AWG |
| C | Battery JST → TP4056 `B+`/`B-` | 40 mm | battery's own leads |
| D | TP4056 `OUT±` → LDO `IN±` (2-pin JST as a disconnect) | 40 mm | 2 × 26 AWG |
| E | LDO `OUT`/`GND` → C3 `3V3`/`GND` | 50 mm | 2 × 26 AWG |
| F | Divider → C3 `GPIO1`/`GND` | 50 mm | 2 × 26 AWG |
| G | C3 `GPIO5`/`GPIO0`/`GND` → probe pigtail | 60 mm | 3 × 26 AWG |
| H | Charge pigtail → TP4056 USB-C | — | use the pigtail's own lead |

Run B is the one that has to be right: it passes through a 5 × 2.2 mm groove, so
bundle the three wires with a light twist and no heatshrink over the bundle until
after the test fit. The bundle must stay under 5 mm across.


## Build order

1. **Solder the charge chain first.** Battery JST → TP4056, then TP4056 → LDO →
   C3. Plug in USB-C and confirm 3.3 V at the LDO output **before** the C3 is
   connected. This is the only step that can kill the board.
2. **Fit the C3 into the bay.** It sits in the printed channel with the USB-C end
   towards the charge-port cut-out and the antenna facing away from the battery.
3. **Battery divider.** 1 MΩ from the cell node to `GPIO1`, 1 MΩ from `GPIO1` to
   GND, 100 nF across the lower resistor, right at the pin.
4. **Probe pigtail.** Solder the three wires to the probe header with the wire
   exiting *towards the pot wall*, so it turns into the groove without a kink.
   Heat-shrink each joint individually, then the bundle.
5. **Feed the probe wires** down through the bay notch, along the leg groove and
   into the probe cavity from above, then seat the probe.
6. **Optional button.** A 6 mm tact switch between `GPIO3` and `GND`, glued into
   the bay's side pocket. Without it everything still works; you just have to
   catch the node in its awake window to reach it OTA.

## Continuity check before first power

With the battery **disconnected**:

- `3V3` to `GND` should read a few hundred kΩ, not 0 Ω. A short here means a
  solder bridge under the C3.
- `GPIO5` to `GND` reads the probe's resistance (hundreds of kΩ to MΩ).
- `GPIO1` to `GND` reads 1 MΩ, and `GPIO1` to the cell node reads 1 MΩ.
- No continuity between `GPIO0` and `GPIO5` — if there is, the probe header is
  bridged and the ADC will read the rail.

## Common wiring mistakes

| Symptom | Cause |
|---|---|
| Battery % stuck at 100 | Divider on the 3.3 V rail instead of the cell node |
| Soil reading pinned at 0 % | Probe VCC wired to `3V3` instead of `GPIO5`, so the rail never switches off and the probe reads a constant 3 V |
| Node browns out when Wi-Fi connects | C3 fed from the 5 V pin with a 3.7 V battery — the LDO is in dropout; use the `3V3` pin via the HT7333 |
| Never wakes on the button | Button on `GPIO9` (BOOT) instead of `GPIO3` |
| Charging LED never turns blue | TP4056 `B±` not connected, or the cell's protection board tripped |

Next: [ASSEMBLY.md](ASSEMBLY.md) for the mechanical build.
