# Using it

## What happens every 30 minutes

```
t+0s      deep-sleep wake (timer, or the wake button)
t+0.1s    probe rail on; battery divider already live
t+0..3s   Wi-Fi associate (fast_connect, stored channel)
t+3..5s   API connects -> hub sees the node, soil + battery published
t+5s      probe sample (16 reads averaged), battery sample
t+30s     deep sleep, run_duration expires
```

Everything between wakes is dark: no Wi-Fi, no probe power, ~45 µA. Home Hub marks
a node's entities **unavailable** the moment it disconnects, so that is what a
sleeping SoilSitter looks like for ~98 % of the day — by design, not a fault. It
reconnects with backoff, logs a disconnect warning each time, and republishes on
the next wake. Do not build an automation that treats `unavailable` as a fault on
this node. To detect a dead unit, watch the age of the last moisture or battery
update ([INTEGRATION.md](INTEGRATION.md)), not the connectivity sensor.

## Entities

| Entity | Kind | Use |
|---|---|---|
| `sensor.<node>_soil_moisture` | `%`, `device_class: moisture` | The one the Garden binds to a plant |
| `sensor.<node>_battery` | `%`, `device_class: battery` | When to charge |
| `sensor.<node>_soil_voltage` | `V`, diagnostic | Calibration |
| `sensor.<node>_battery_voltage` | `V`, diagnostic | Divider sanity check |
| `sensor.<node>_wifi_signal` | dBm, diagnostic | Where to hang the pot |
| `sensor.<node>_uptime` | s, diagnostic | Confirms the node is cycling, not stuck |
| `binary_sensor.<node>_online` | connectivity | True only while awake; unavailable between wakes, so do not alert on it |
| `switch.<node>_stay_awake` | switch | Disables deep sleep; auto-off after 10 min |
| `button.<node>_sleep_now` | button | Sleep immediately, do not wait the window |
| `button.<node>_restart` / `_safe_mode` | buttons | Recovery |

`<node>` is `soilsitter-<6 hex>` because `name_add_mac_suffix: true` is set, so two
builds in one house never collide. The hostname is `soilsitter-<6 hex>.local`.

## Placing it

- **Hang it on the side of the pot that faces away from the room.** That is the
  whole point: the bay and the wires disappear behind the pot, and the probe is the
  only thing inside.
- **Sun on the bay is bad.** A dark PETG bay in direct summer sun reaches 60 °C, and
  a LiPo above 45 °C ages fast. Shade the bay, or use ASA and accept a shorter cell
  life.
- **Distance**: the C3's PCB antenna is at the top of the bay, facing away from the
  pot, so one wall at ~10 m is fine. Check `Wi-Fi Signal`: below −80 dBm the wake
  window starts to miss publishes.
- **Watering**: the probe reads what surrounds it. Watering right beside the sleeve
  gives a spike for a few hours, then the real reading returns. For a plant on a
  schedule, compare the same hour of the day.
- **Do not move it between pots** without re-seating the probe: the hook is cut for
  one rim thickness, and the probe's contact pressure matters.

## Charging

- The charge port is the M16 pigtail in the bay's outer wall. Any 5 V USB-C source;
  the TP4056 draws up to 1 A, so a phone charger is fine.

## Battery life

Per wake, with the firmware's defaults (30 s window, 30 min interval):

| Item | Energy |
|---|---|
| Wi-Fi associate, 3 s @ ~70 mA | 0.058 mAh |
| Awake 30 s @ ~15 mA average (modem sleep) | 0.125 mAh |
| Probe, 3 s @ 5 mA | 0.004 mAh |
| **Per wake** | **~0.19 mAh** |
| 48 wakes/day | 9.0 mAh |
| Deep sleep, 45 µA | 1.1 mAh |
| **Per day** | **~10 mAh** |
| Usable capacity, 2000 mAh to 80 % DoD | 1600 mAh |
| **Estimate** | **~160 days, call it 4–6 months** |

These are datasheet-and-arithmetic numbers, not a discharge test — nobody has run a
full cycle on this build yet. Treat 4–6 months as the expectation and the Battery
entity as the truth.

Levers, in order of effect:

| Change | Effect |
|---|---|
| Remove the power LED (below) | Doubles run time if your board has one |
| `sleep_interval: 15min` | Halves it, to ~2.5 months |
| `sleep_interval: 60min` | Doubles it, to ~9 months |
| `run_window: 20s` | +25 %, at the cost of OTA headroom |
| `sleep_interval: 5min` | ~1 month. For debugging, not for a shelf |

Soil moisture moves over hours. There is no reason to sample it every five minutes,
and every reason not to.

### The power LED

Most C3 SuperMini clones have a red LED that is **not** on GPIO8 but hard-wired from
the 3.3 V rail through a resistor — it burns ~1 mA forever, which is 24 mAh a day and
half your battery life. Check with the unit asleep: if the LED is still lit, it is
the always-on kind.

Flick it off with a scalpel (it sits proud of the board and the pad survives) or
desolder it. Do this **before** the battery is connected, and check with a multimeter
that you have not bridged the 3.3 V rail to ground. The GPIO8 LED, if your board has
one, costs nothing while the node sleeps — leave it.

## Recovery

| Situation | What to do |
|---|---|
| Node will not answer for OTA | Press the wake button (or short `GPIO3` to GND) and run `esphome run` within 10 minutes |
| Wrong Wi-Fi credentials | Fallback AP `soilsitter-<hex> fallback`, password `ap_password`; join it and the captive portal opens |
| Firmware misbehaving | `button.<node>_safe_mode` over the API, or hold the C3's BOOT button while power-cycling |
| Recovering a bricked node | The C3's own USB-C is reachable with the lid off — it is native USB-Serial-JTAG, no UART adapter needed |
| Battery died and it forgot everything | It did not: Wi-Fi, API key and calibration all live in flash |

## Quirks worth knowing

- **The first boot never sleeps** until the hub connects once (`api.on_client_connected`
  sets `provisioned`). Deliberate: adoption needs more than 30 seconds.
- **Restart does not lose the sleep schedule**, but the node comes back with a fresh
  run window.
- **Safe Mode keeps the sensors off** (it boots with no custom components), which is
  what you want when a config change is at fault.
- **Two units on the same shelf** keep distinct entity ids thanks to the MAC suffix;
  just bind the right one in the Garden.
- **Water on the gasket** is fine; water *in* the bay is not. If the lid gasket is
  compressed to nothing, the screws are too tight or the gasket is too thin.

Next: [INTEGRATION.md](INTEGRATION.md) to bind it to a plant.

- The TP4056's LEDs are only visible with the lid off, so in practice: **charge when
  Battery drops below 20 %**, unplug after ~3 h. A 2000 mAh cell from 20 % takes
  about 1 h 40 m at 1 A.
- **Never charge below 0 °C.** If the pot lives outside and it is freezing, bring the
  unit in to charge and let it warm up first. Charging a cold LiPo plates lithium
  metal and permanently loses capacity.
- Charging while the node sleeps is fine: the TP4056 charges the cell directly.
