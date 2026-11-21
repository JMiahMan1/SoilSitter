# Changelog

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
