# Fridge Dashboard

A full-screen dashboard (time, power, temperature, humidity) for a wall or fridge-mounted
tablet optimized to run on old browsers.

## Configuration

Add these sensors to be shown in the dashboard:

| Option | Description |
| --- | --- |
| `entity_temperature` | Temperature sensor entity ID (e.g. `sensor.fridge_temperature`) |
| `entity_humidity` | Humidity sensor entity ID |
| `entity_power` | Power-consumption sensor entity ID (optional — leave empty and the clock fills the left column) |
| `page_refresh_interval_seconds` | Whole-page refresh interval (default 60, min 5) |
| `theme` | Color theme: `dark` (default) or `light` |

Units (°C, %, W etc) come from each entity's `unit_of_measurement`. A sensor that can't be
read shows `--`; if Home Assistant is unreachable an offline page is shown and recovers
automatically once Home Assistnat is reachable again.

## Use

1. Set the three sensors on the **Configuration** tab and **Start** the add-on.
2. On the tablet, open `http://<home-assistant-ip>:6123/`.
