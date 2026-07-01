# Changelog

## 1.1.0

- Make the power sensor optional. Leave `entity_power` empty and the clock fills
  the whole left column; set it to restore the clock-over-power split.

- Add a **Theme** option (`dark` default / `light`) — a light Apple-style palette.

## 1.0.0

- Initial add-on release: full-screen fridge dashboard (time, power, temperature, humidity).
- Talks to Home Assistant via the Supervisor API; only the sensor entity IDs are configured.
- Prebuilt `aarch64` / `amd64` images.
