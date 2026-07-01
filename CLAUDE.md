# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python Flask web server that renders a Home Assistant dashboard for an **iPad mini (1st
generation)** mounted on a fridge. The server fetches three sensors (temperature, humidity,
power consumption) from Home Assistant's REST API and renders a server-side HTML page styled
as dark Apple-style widgets. The iPad connects over the LAN to
`http://<host>:<SERVER_PORT>/`.

The target browser is **Safari 9 (iOS 9)** — the iPad mini 1's maximum. It supports flexbox,
`border-radius`, `box-shadow`, `@font-face`, and ES5 JavaScript, but **not CSS Grid or CSS
custom properties**. Keep the HTML/CSS/JS deliberately simple and backward-compatible.

## Commands

Dependencies are managed with **uv**. Always prefer `make` targets.

```bash
make setup          # uv sync — create venv + install all deps (incl. dev)
make run            # Flask dev server on 0.0.0.0:$SERVER_PORT
make test           # full pytest suite
make lint           # ruff check + ruff format --check
make format         # ruff --fix + ruff format
make quality        # lint then format
make docker-up      # build + run via Docker Compose (recommended deploy)
make docker-build   # build image only
make docker-down    # stop containers
```

Single test: `uv run pytest tests/test_client.py::test_get_state_non_200 -v`

## Configuration

All configuration comes from **environment variables** (no `constants.py`). See
`.env.example` and the README table. Required: `HASS_IP`, `HASS_PORT`, `HASS_TOKEN`,
`ENTITY_TEMPERATURE`, `ENTITY_HUMIDITY`, `ENTITY_POWER`. Optional:
`PAGE_REFRESH_INTERVAL_SECONDS` (default 60), `SERVER_PORT` (default 6123). `config.py`
validates these at startup and fails fast listing any that are missing. The real `.env` is
gitignored.

This repo is also a **Home Assistant add-on repository**: `repository.yaml` at the root and
the add-on manifest at `fridge_dashboard/config.yaml`. Only the sensor entity IDs (+ refresh)
are set in HA's Configuration UI; HA writes them to `/data/options.json` and `entrypoint.sh`
maps each key to its upper-cased env var (e.g. `entity_temperature` → `ENTITY_TEMPERATURE`).
With `homeassistant_api: true`, `entrypoint.sh` also points `HASS_URL` at the Supervisor
proxy (`http://supervisor/core/api/`) using the injected `SUPERVISOR_TOKEN`, so no host,
port, or token is configured. The manifest's `image:` is a prebuilt GHCR image built by
`.github/workflows/build-image.yaml` (buildx, `aarch64`/`amd64`) on push to `main`; bump
`fridge_dashboard/config.yaml`'s `version` to ship an update.

## Architecture

**Request flow:** iPad → Flask (`app.py`) `GET /` → `HassClient.is_reachable()`. If
unreachable, render `offline.html`; otherwise `build_dashboard_model()` fetches each sensor
via `HassClient.get_state()` and renders `dashboard.html` (with a `<meta http-equiv=refresh>`
and the ES5 clock).

### Key files

- **`app.py`** — Flask entry point. Routes: `/` (dashboard or offline), `/health` (liveness).
  The module-level `_client` is the `HassClient`; tests patch it.
- **`config.py`** — `load_config() -> Config` reads/validates env vars. Raises `ConfigError`.
- **`homeassistant/client.py`** — `HassClient`. `get_state(entity_id)` returns
  `{"result", "state", "unit"}` (reading HA's `unit_of_measurement`) or `{"result": "err"}`;
  `is_reachable()` health-checks HA. Bearer-token auth, 5s timeout.
- **`dashboard/view.py`** — `build_dashboard_model(client, config, now)` builds the template
  view model; a failed sensor becomes `{"value": "--", "unit": "", "ok": False}`.
- **`templates/`** — `dashboard.html`, `offline.html`, shared `_head.html`.
- **`static/css/styles.css`** — dark theme; **flexbox only, no grid / custom properties**.
- **`static/js/clock.js`** — ES5 only; ticks the `#clock` element each second.
- **`static/assets/`** — `thermometer.svg`, `droplet.svg` (colors hardcoded in the SVG, since
  `<img>`-loaded SVGs can't be recolored by host CSS), `favicon.ico` (linked from `_head.html`).

### Design constraints

- Table-based skeleton + flexbox card interiors for old-Safari reliability.
- **No CSS Grid, no CSS custom properties (`var()`), ES5 JavaScript only.**
- Dark theme only. Production uses Gunicorn (see `Dockerfile`).

## Conventions

- **uv** for dependencies; `uv.lock` is committed.
- **Make-first**: use `make` targets instead of raw commands when one exists.
- **TDD**: write a failing test before implementation (`superpowers:test-driven-development`).
- **Code style**: see `context/styling/formatting.md` (snake_case functions, PascalCase
  classes, Google-style docstrings, ruff line-length 120).
- **No auto-commits**: never run `git commit`/`git push` unless the user explicitly asks.

## Planning Workflow

All design docs and plans live under `context/planning/` (this overrides any skill default
such as `docs/superpowers/`). The design and the implementation checklist for a task live in
the **same** file — design first, implementation checklist appended after approval. Plans are
committed alongside code and never deleted.

## Superpowers Skills

Use proactively: `brainstorming` (before creative work), `writing-plans` (before multi-step
tasks), `test-driven-development` (when implementing), `systematic-debugging` (on any bug),
`verification-before-completion` (before claiming done).
