# Calibration

The sensor reports a percentage, and a percentage is only meaningful if two
voltage end points have been measured on **your** probe. Every V1.2 board differs
by ±0.2 V, potting soil differs by more, so the firmware's defaults are a starting
point, not a calibration.

The defaults in `firmware/soilsitter.yaml`:

```yaml
soil_dry_voltage: "2.55"   # dry potting soil, probe seated to depth
soil_wet_voltage: "1.15"   # just-watered soil, drained for an hour
```

`calibrate_linear` maps dry → 0 % and wet → 100 %, and a `clamp` keeps noise from
reporting −3 % or 104 %.

## What "dry" and "wet" mean here

Not air and not a glass of water.

- **Air** reads 2.6–2.8 V on a V1.2 and is *drier than any soil you will own*. Calibrating
  against air makes every real pot read 30–60 % and you will drown your plants.
- **Water** reads about 1.0–1.2 V and is wetter than any soil; a pot that wet is
  already anaerobic.

Use soil. Two samples, both in the pot the sensor will live in, at the depth the
sleeve puts the probe (~60 mm below the rim):

1. **Dry**: let the pot go until the plant is *just* at the point where you would
   water it. That is your 0 %.
2. **Wet**: water thoroughly, let it drain an hour, then measure. That is 100 %.

If you want a wider working range, use "bone dry, a week past watering" for 0 %
and "freshly watered, drained" for 100 %; the numbers barely change.

## Procedure

1. Flash the firmware and put the node on the bench with the probe in the pot.
2. In Home Hub (or `esphome logs soilsitter.yaml`), turn on **Stay Awake**. The node
   stops sleeping and the two ADC sensors refresh every 60 s.
3. Let the pot dry to your 0 % point. Read **Soil Voltage** — this is
   `soil_dry_voltage`. Take three readings a minute apart; they should agree to
   ±0.01 V. If they wander, the probe is not seated and the contact is intermittent.
4. Water, wait an hour, read **Soil Voltage** again — that is `soil_wet_voltage`.
5. Put both numbers in the substitutions, then reflash (`esphome run`). **Soil
   Moisture** should now read 0 % dry and 100 % wet.
6. Turn **Stay Awake** off. The node sleeps and the numbers keep their meaning.

The two voltages are also exposed as diagnostic entities, so after calibration
you can sanity-check a drifted reading without pulling the probe.

## Sanity table

For a V1.2 powered at 3.3 V, with the sensing face against the soil:

| Condition | Typical voltage | Percentage after the default calibration |
|---|---|---|
| Air / probe not in soil | 2.60–2.80 V | 0 % (clamped) |
| Bone-dry potting mix | 2.45–2.60 V | 0–7 % |
| Dry-ish, ready to water | 2.20–2.40 V | 10–25 % |
| Freshly watered, drained | 1.30–1.60 V | 65–90 % |
| Saturated / standing in water | 1.00–1.20 V | 100 % (clamped) |

If your probe reads outside these bands by more than 0.3 V, check the wiring
before calibrating: an AOUT/VCC swap reads a constant ~3.0 V, and a floating ADC
reads noise.

## Battery curve

The battery percentage is a straight line between the cell's empty and full
voltages, measured **at the cell** through the 1 MΩ divider:

```yaml
battery_empty_voltage: "3.30"
battery_full_voltage: "4.15"
```

That is deliberate: a Li-ion discharge curve is flat enough between 3.7 and 3.9 V
that a lookup table buys you nothing on a node that reports every 30 minutes, and
a straight line never lies about *empty*, which is the number that matters. Expect
the percentage to sit at 60–70 % for weeks and then fall quickly — that is the
chemistry, not the firmware.

Measure the two end points with a multimeter if you care:

- **Full**: right after the TP4056's LED turns blue, no load.
- **Empty**: when the node starts brown-out rebooting (about 3.3 V under load).
  Do not take a cell below 3.0 V; the TP4056's DW01 cuts off at 2.5 V, which is
  already too deep for a pouch cell's cycle life.

## Recalibrating

Soil sensors drift, and the drift is mostly the electrode's potting compound
absorbing water. Expect 0.05–0.1 V over a year. Recalibrate when a plant you know
is thirsty reads above 40 %, or simply re-measure dry soil once a season and nudge
`soil_dry_voltage`.

The probe itself is the consumable: the V1.2's gold-plated electrode is rated for
3–5 years of continuous power. This build only powers it for ~2 minutes a day, so
the electrode should outlast the battery.

Next: [USAGE.md](USAGE.md).
