# Changelog

## 1.2.1

- Bug fixes and experience improvements.

## 1.2.0

- Add optional trend arrows. Set `entity_temperature_derivative` and/or
  `entity_humidity_derivative` to a Home Assistant derivative sensor and a
  gray arrow below the value shows the trend (↗ rising, ↘ falling, → stable).
  Leave them empty and the dashboard looks exactly as before.

## 1.1.2

- Color the temperature icon by its reading: green when 1 °C ≤ temp ≤ 4 °C,
  red otherwise.
- Add an add-on icon.

## 1.1.0

- Make the power sensor optional. Leave `entity_power` empty and the clock fills
  the whole left column; set it to restore the clock-over-power split.

- Add a **Theme** option (`dark` default / `light`) — a light Apple-style palette.

## 1.0.0

- Initial add-on release: full-screen fridge dashboard (time, power, temperature, humidity).
- Talks to Home Assistant via the Supervisor API; only the sensor entity IDs are configured.
- Prebuilt `aarch64` / `amd64` images.
