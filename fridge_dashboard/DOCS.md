# Fridge Dashboard
A tiny Python/Flask web server that renders a single full-screen dashboard (time, power, temperature, humidity) for a wall or fridge-mounted
tablet optimized to run on old browsers.

## Configuration

Add these sensors to be shown in the dashboard:

| Option | Description | Optional |
| --- | --- | --- |
| `entity_temperature` | Temperature sensor entity ID (e.g. `sensor.fridge_temperature`) | **No** |
| `entity_humidity` | Humidity sensor entity ID | **No** |
| `entity_power` | Power-consumption sensor entity ID | Yes |
| `entity_temperature_derivative` | Derivative (rate-of-change) sensor for temperature. Set it to show a trend arrow below the number (↗ rising, ↘ falling, → stable) | Yes |
| `entity_humidity_derivative` | Derivative sensor for humidity, same trend arrow behaviour | Yes |
| `page_refresh_interval_seconds` | Whole-page refresh interval (default 60, min 5) | Yes |
| `theme` | Color theme: `dark` (default) or `light` | **No** |

Units (°C, %, W etc) come from each entity's `unit_of_measurement`. A sensor that can't be
read shows `--`; if Home Assistant is unreachable an offline page is shown and recovers
automatically once Home Assistnat is reachable again.

## Use

1. Set the sensors on the **Configuration** tab and **Start** the add-on.
2. On the tablet, open `http://<home-assistant-ip>:6123/`.

## Port

The dashboard is served on host port **6123** by default. If that port is already in use,
open the add-on's **Network** panel and set any free host port, then browse to
`http://<home-assistant-ip>:<that-port>/`. See the logs to verify the port is free.
