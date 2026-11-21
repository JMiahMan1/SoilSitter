# Home Hub and Garden integration

SoilSitter speaks the ESPHome native API. That is the only integration path it
needs: [SharedLLM](../../SharedLLM)'s Home Hub adopts ESPHome nodes directly over the
API (no HA in the middle), and its Garden binds the `moisture` sensor to a plant.

Two things make it work, and both are already in the firmware:

- `api: encryption: key:` — the hub refuses a node it cannot authenticate, and the
  key you paste into the hub is the same `api_encryption_key` from `secrets.yaml`.
- `device_class: moisture` on the percentage sensor — the Garden classifies live
  sensors by device class (falling back to "soil"/"moisture" in the entity name),
  so this is what puts SoilSitter in the moisture list instead of the generic one.

## 1. Get the node on the network

```bash
cd firmware
cp secrets.yaml.example secrets.yaml
$EDITOR secrets.yaml        # Wi-Fi, AP password, API key, OTA password
esphome run soilsitter.yaml # first flash over the C3's own USB-C
```

Then, on first boot only, the node **stays awake** — `api.on_client_connected`
sets the `provisioned` global the first time anything connects, and until then
`deep_sleep.prevent` holds it up. That gives you an unbounded window to adopt it.
After that first connection it keeps the flag in NVS and sleeps between
measurements.

## 2. Adopt it in Home Hub

1. Home Hub → **Devices** → **Discovered**. The node advertises
   `_esphomelib._tcp.local.` and appears as `soilsitter-<hex>` (with its IP).
2. **Add**. Because the firmware is encrypted, the hub asks for the **noise PSK**:
   paste `api_encryption_key` from `secrets.yaml`.
3. Pick an area (the room the plant lives in). The entity list is read live from
   the node, so the sensors appear immediately.

If mDNS does not reach the hub (a VLAN, or a busy Docker bridge), add it manually
with **host** = `soilsitter-<hex>.local` (or its IP) and the same key. A node that
has been flashed twice shows up as a *new* device if its MAC changed; delete the
old entry first — the hub returns `409 This ESPHome node is already set up`
otherwise.

Once adopted, the entities are named `sensor.soilsitter_<hex>_soil_moisture`,
`sensor.soilsitter_<hex>_battery`, and so on. The hub reads them over the Noise
channel every time the node wakes.

> **Unavailable is normal.** A sleeping node has no connection. The hub keeps the
> last state with a last-seen time and only marks it unavailable when a wake
> window is missed. Do not build an automation that treats `unavailable` as a
> fault on a 30-minute node.

## 3. Bind it to a plant in the Garden

1. Garden → **Plants** → the plant → **Home Hub** binding card. (The card only
   appears once the hub has any hardware at all — that is the Garden's progressive
   disclosure, not a bug.)
2. **Soil moisture** → pick `sensor.soilsitter_<hex>_soil_moisture`.
3. Set the **threshold** (30 % is a good start) and enable the moisture override.

What the Garden then does, in `services/garden/homehub_hardware.py`:

| Reading | Garden's verdict |
|---|---|
| below the threshold | watering is **due** now: "Soil moisture is 21 % (below 30 %)" |
| at least threshold + 15 % | **holding off**: "Soil moisture is 68 % — holding off" |
| between the two | neither forced nor held; the normal cadence stands |
| sensor not reporting | the normal schedule applies, and the card says the sensor is offline |

The band exists so a plant does not flip between due and held every 30 minutes as
the reading wobbles. The opt-in flag matters: without it, the sensor is only a
display pill and never changes a schedule.

The same live percentage feeds the plant card's `💧` pill and `live_moisture_pct`
in `GET /today`, which is what Jarvis answers with when you ask "does the monstera
need water?".

## 4. Useful automations

Written against Home Hub's entity ids; adjust `<hex>`.

```yaml
# Charge reminder: below 20 % while the plant is still fine
trigger: numeric_state, sensor.soilsitter_<hex>_battery, below: 20
action:  notify "SoilSitter on the monstera is at 18 % — charge it"

# Dead node: no update for two hours (four wake windows)
trigger: state, binary_sensor.soilsitter_<hex>_online, to: "off", for: "2:00:00"
action:  notify "SoilSitter stopped reporting"

# Prime the pump before a heatwave
trigger: numeric_state, sensor.soilsitter_<hex>_soil_moisture, below: 25
action:  garden.log_care(plant, watered)  # or a valve run on a bound bed
```

Avoid automations that *act* on every moisture reading: the reading is up to 30
minutes old by design, and a watering decision made on a stale dry value is how
plants get drowned.

## 5. Day-to-day commands

| Want | Do |
|---|---|
| Live reading now | Press the wake button, or turn on **Stay Awake**, then read |
| Recalibrate | **Stay Awake** on, read **Soil Voltage**, update the two substitutions, OTA |
| Firmware update | **Stay Awake** on (or press the wake button), then `esphome run` or Home Hub's OTA |
| Take it off a plant | Delete the Garden binding first; the entity stays in the hub |
| Retire the node | Delete the Home Hub entry; nothing in the Garden holds a copy |

OTA from Home Hub (`POST /api/mdm/esphome/{device}/ota`) works on this node because
it exposes the standard native OTA on port 3232 with `ota_password`. Upload
`firmware/.esphome/build/soilsitter/build/firmware.ota.bin` (ESPHome names the OTA
image separately from the factory image you would flash over USB). The deep-sleep
guards around OTA (`on_begin: prevent`, `on_end: enter`) keep the node awake for
the length of the transfer, and the transfer is < 2 minutes on a normal network.
