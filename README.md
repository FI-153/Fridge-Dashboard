# Fridge Dashboard

A tiny Python/Flask web server that renders a single full-screen dashboard for an
**iPad mini (1st generation)** mounted on a fridge. It reads three sensors from
Home Assistant and shows them as dark, Apple-widget-style cards:

- **Time** — a live digital clock (top-left)
- **Power consumption** — current draw (bottom-left)
- **Temperature** — centre, with a thermometer icon
- **Humidity** — right, with a water-drop icon

```
+-------------+---------------+-------------+
|   21:28     |               |             |
|.............|   [thermo]    |   [drop]    |
|             |     4.2°C     |    58%      |
|   POWER     |               |             |
|   120 W     |               |             |
+-------------+---------------+-------------+
```

The HTML/CSS/JS are deliberately minimal so they render on Safari 9 (the iPad mini 1's
maximum iOS). The whole page meta-refreshes every minute to pull fresh sensor values, and a
~10-line ES5 script keeps the clock ticking between refreshes.

## How the iPad connects

Point the iPad's browser at the server over your LAN:

```
http://<server-host-or-ip>:<SERVER_PORT>/
```

`SERVER_PORT` defaults to `6123`.

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` and fill it in:

| Variable                        | Required | Default | Purpose                                  |
| ------------------------------- | -------- | ------- | ---------------------------------------- |
| `HASS_IP`                       | yes\*    | —       | Home Assistant host/IP                   |
| `HASS_PORT`                     | yes\*    | —       | Home Assistant port                      |
| `HASS_TOKEN`                    | yes      | —       | Long-lived access token                  |
| `ENTITY_TEMPERATURE`            | yes      | —       | Temperature sensor entity ID             |
| `ENTITY_HUMIDITY`               | yes      | —       | Humidity sensor entity ID                |
| `ENTITY_POWER`                  | yes      | —       | Power-consumption sensor entity ID       |
| `HASS_URL`                      | no       | —       | Full API base (`…/api/`); if set, replaces `HASS_IP`/`HASS_PORT` |
| `PAGE_REFRESH_INTERVAL_SECONDS` | no       | `60`    | Whole-page refresh interval (seconds)    |
| `SERVER_PORT`                   | no       | `6123`  | Port the dashboard is served on          |

\* `HASS_IP`/`HASS_PORT` are only needed when `HASS_URL` is not set. As a Home Assistant
add-on the app talks to Core through the Supervisor proxy, so none of the connection
variables are configured by hand — only the sensors (see below).

Units (°C, %, W, …) are read from each entity's Home Assistant `unit_of_measurement`
attribute, so nothing is hardcoded. If a sensor can't be read, its card shows `--`; if
Home Assistant is entirely unreachable, an offline page is shown and the dashboard recovers
automatically on the next refresh.

## Deployment (Docker — recommended)

The image is configured entirely through **runtime environment variables** — there is no
baked-in config and **no `.env` file is required**. Provide the variables whichever way suits
you.

**A. Run the image directly** (e.g. after pulling/loading it):

```bash
docker run -d --name fridge_dashboard -p 6123:6123 \
  -e HASS_IP=192.168.1.10 \
  -e HASS_PORT=8123 \
  -e HASS_TOKEN=your-long-lived-token \
  -e ENTITY_TEMPERATURE=sensor.fridge_temperature \
  -e ENTITY_HUMIDITY=sensor.fridge_humidity \
  -e ENTITY_POWER=sensor.fridge_power \
  fridge-dashboard
```

**B. Docker Compose.** The bundled `docker-compose.yaml` reads the variables from your shell
(or an optional `.env` in the directory, which Compose auto-loads) and applies sensible
defaults for the optional ones, so it works with or without a `.env`:

```bash
export HASS_IP=192.168.1.10 HASS_PORT=8123 HASS_TOKEN=... \
  ENTITY_TEMPERATURE=sensor.fridge_temperature \
  ENTITY_HUMIDITY=sensor.fridge_humidity \
  ENTITY_POWER=sensor.fridge_power
make docker-up              # build + run in the background
```

Or just drop the values into your own `compose.yaml` under `environment:`. The container's
launch command lives in `entrypoint.sh`.

The dashboard is then available at `http://<host>:<SERVER_PORT>/`.
Stop it with `make docker-down`. A liveness probe is exposed at `/health`.

## Install as a Home Assistant add-on

This repo is also a Home Assistant **add-on** (`config.yaml`), so it can be installed and
configured straight from the Home Assistant UI — including the **sensor entity IDs**.

1. Copy this repo into your Home Assistant `/addons` folder, e.g. via the *Samba* or
   *Advanced SSH & Web Terminal* add-on:
   ```bash
   git clone https://github.com/FI-153/Fridge-Dashboard /addons/fridge-dashboard
   ```
2. **Settings → Add-ons → Add-on Store → ⋮ → Check for updates**. "Fridge Dashboard" now
   appears under **Local add-ons**. Open it and click **Install** (it builds on the device;
   `aarch64`/`amd64`).
3. On the **Configuration** tab, set the three sensors (`entity_temperature`,
   `entity_humidity`, `entity_power`) and optionally the refresh interval — then **Start**.
   The add-on reaches Home Assistant through the Supervisor API, so there is **no host, port,
   or token to enter**.
4. On the tablet, open `http://<home-assistant-ip>:6123/`.

Changing the sensors later is just editing those fields and restarting the add-on — no files
to touch. (Bump `version` in `config.yaml` when you pull new code so HA offers the update.)

## Local development

Dependencies are managed with [uv](https://docs.astral.sh/uv/).

```bash
make setup    # create the virtualenv and install deps (uv sync)
make test     # run the test suite
make lint     # ruff lint + format check
make format   # auto-fix + format
```

To run the dev server locally:

```bash
make debug    # loads ./.env if present, then runs the Flask dev server in the terminal
make run      # runs the Flask dev server (expects the variables already exported)
```

## Project layout

```
app.py                    Flask entry point + routes
config.py                 Loads/validates env-var configuration
homeassistant/client.py   Home Assistant REST client
dashboard/view.py         Builds the template view model
templates/                Jinja2 templates (dashboard, offline, shared head)
static/css/styles.css     Dark Apple-widget styling (Safari-9 safe)
static/js/clock.js        ES5 ticking clock
static/assets/            SVG icons + favicon
tests/                    pytest suite
context/                  Design docs and conventions
```
