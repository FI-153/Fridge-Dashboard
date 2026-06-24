# Fridge Dashboard — Design

## Overview

A Python Flask web server that renders a single full-screen dashboard for an
**iPad mini (1st generation)** mounted on a fridge. The iPad's browser is Safari 9
(iOS 9, the device's maximum) — capable but old: it supports flexbox, `border-radius`,
`box-shadow`, gradients, `@font-face`, and ES5 JavaScript, but **not** CSS Grid or
CSS custom properties. The dashboard must therefore stay deliberately simple.

The server fetches three sensor values from Home Assistant's REST API and renders a
server-side HTML page styled to look like Apple widgets (dark theme). The iPad connects
to the server over the LAN at `http://<server-host>:<SERVER_PORT>/`.

This project takes architectural inspiration from the sibling `eInk_dashboard` project
(Flask + Gunicorn, server-side HTML, meta-refresh, `HassCommunicationsCoordinator`
REST client, Makefile-driven workflow), with three deliberate differences:

1. **Configuration via environment variables** (not a `constants.py` file).
2. **Dependencies managed with `uv`** (not pip/`requirements.txt`).
3. **HTML rendered with Jinja2 templates** (not a string-based tag builder), and a
   **color** dark theme (the iPad has a color screen, unlike the e-ink reference).

## Sensors displayed

| Sensor          | Env var for entity ID | Display                                  |
| --------------- | --------------------- | ---------------------------------------- |
| Temperature     | `ENTITY_TEMPERATURE`  | Thermometer icon on top, big value below |
| Humidity        | `ENTITY_HUMIDITY`     | Water-drop icon on top, big value below  |
| Power consumption | `ENTITY_POWER`      | Big value, bottom half of the left column |

Units are read from each entity's Home Assistant `unit_of_measurement` attribute, so
they are not hardcoded (e.g. `°C`, `%`, `W`).

## Layout

A full-width, full-height HTML `<table>` of **three columns** (chosen for maximum
reliability on the old Safari engine). Each cell's inner content is styled as a rounded,
dark "card" to achieve the Apple-widget look, with gaps between cards.

Left → right:

```
+-------------+---------------+-------------+
|   12:45     |               |             |   left card, TOP half: clock
|.............|   [thermo]    |   [drop]    |   (clock split from power by a divider)
|             |               |             |
|   POWER     |    4.2°       |    58%      |   center: temperature   right: humidity
|   120 W     |               |             |   (icon on top, big number below)
+-------------+---------------+-------------+
```

- **Left column** — a single full-height cell split horizontally into two halves
  (flexbox column): the digital **clock** on the top half, **power consumption** on the
  bottom half.
- **Center column** — temperature: thermometer icon on top, big number below, centered.
- **Right column** — humidity: water-drop icon on top, big number below, centered.

The clock uses large, bold **monospace** digits (no embedded font file).

## Architecture

```
iPad Safari 9  →  Flask (app.py) on $SERVER_PORT  →  GET "/"
                      │
                      ├─ HassClient.is_reachable()? ── no ─→ render offline.html
                      │
                      └─ yes → fetch 3 sensors → build view model → render dashboard.html
```

### Components

- **`config.py`** — single source of truth for configuration. Reads and validates all
  environment variables at import/startup. Raises a clear error listing any missing
  required variables (fail fast). Holds: HA connection (`HASS_IP`, `HASS_PORT`,
  `HASS_TOKEN`), entity IDs (`ENTITY_TEMPERATURE`, `ENTITY_HUMIDITY`, `ENTITY_POWER`),
  `PAGE_REFRESH_INTERVAL_SECONDS` (default 60), `SERVER_PORT` (default 6123).

- **`homeassistant/client.py`** (`HassClient`) — Home Assistant REST client.
  - `get_state(entity_id) -> dict` — fetches an entity's state with Bearer-token auth and
    a 5s timeout. Returns `{"result": "OK", "state": <str>, "unit": <str|None>}` on
    success (reading the `unit_of_measurement` attribute), or `{"result": "err"}` on any
    failure (connection error, non-200, entity not found, `unavailable` state).
  - `is_reachable() -> bool` — GETs the API root; `True` only on HTTP 200.

- **`dashboard/view.py`** — builds the dashboard view model. Calls `HassClient.get_state`
  for each of the three sensors and produces a small structure per sensor
  (`value`, `unit`, `ok` flag) plus the server-rendered initial clock time. Keeps all
  Home-Assistant-shape knowledge out of the templates.

- **`app.py`** — Flask entry point. Routes:
  - `/` — if HA is unreachable, render `offline.html`; otherwise build the view model and
    render `dashboard.html`.
  - `/favicon.ico` — serve the static favicon.
  - Static files served from `static/`.
  - Dev server (`python app.py` / `make run`) binds `0.0.0.0:$SERVER_PORT`. In Docker,
    Gunicorn binds the same port.

- **`templates/dashboard.html`**, **`templates/offline.html`** — Jinja2 templates.
- **`templates/_head.html`** (or a shared block) — stylesheet link, viewport meta, and the
  `<meta http-equiv="refresh">` tag, shared by both pages.
- **`static/css/styles.css`** — dark Apple-widget styling, flexbox only.
- **`static/js/clock.js`** — ~10 lines of ES5 that update the clock text every second.
- **`static/assets/thermometer.svg`**, **`droplet.svg`**, **`favicon.ico`**.

## Styling

- Dark theme: near-black page background, dark-grey rounded cards with soft `box-shadow`,
  bright values, a subtle accent color. Chosen for an always-on display (low glare).
- **Flexbox only** for inner alignment. **No CSS Grid. No CSS custom properties.** Both are
  unsupported on Safari 9.
- Big values via large `font-size` / `font-weight`. Icons are bundled SVGs, recolorable via
  CSS (`fill`/`currentColor`).
- The `<table>` provides the 3-column full-screen skeleton; visible card styling lives on
  inner `<div>`s, not on table borders.

## Refresh & clock

- `<meta http-equiv="refresh" content="$PAGE_REFRESH_INTERVAL_SECONDS">` reloads the whole
  page (and thus re-fetches sensor data) every ~60s.
- `clock.js` updates the clock element's text every second so the time ticks smoothly
  between reloads. The server also renders an initial correct time into the element, so the
  clock is right even before/without JS.

## Error handling

- **Per-sensor failure** — if a single sensor fetch fails, that card displays `--` and the
  rest of the dashboard renders normally.
- **Home Assistant unreachable** — `/` renders a centered offline card showing the current
  time. The meta-refresh means the dashboard auto-recovers when HA returns.

## Configuration (environment variables)

| Variable                        | Required | Default | Purpose                                   |
| ------------------------------- | -------- | ------- | ----------------------------------------- |
| `HASS_IP`                       | yes      | —       | Home Assistant host/IP                    |
| `HASS_PORT`                     | yes      | —       | Home Assistant port                       |
| `HASS_TOKEN`                    | yes      | —       | Long-lived access token                   |
| `ENTITY_TEMPERATURE`            | yes      | —       | Temperature sensor entity ID              |
| `ENTITY_HUMIDITY`               | yes      | —       | Humidity sensor entity ID                 |
| `ENTITY_POWER`                  | yes      | —       | Power-consumption sensor entity ID        |
| `PAGE_REFRESH_INTERVAL_SECONDS` | no       | `60`    | Whole-page meta-refresh interval          |
| `SERVER_PORT`                   | no       | `6123`  | Port the dashboard is served on           |

A committed **`.env.example`** documents all variables; the real **`.env`** is gitignored.
`docker-compose.yaml` loads the `.env` file.

## Tooling & packaging

- **uv** for dependency management: `pyproject.toml` declares runtime deps (`flask`,
  `requests`, `gunicorn`) and a dev dependency group (`pytest`, `ruff`); `uv.lock` is
  committed.
- **Dockerfile** — uv-based image: `uv sync --frozen`, then runs Gunicorn binding
  `$SERVER_PORT`.
- **docker-compose.yaml** — builds the image, loads `.env`, publishes `$SERVER_PORT`,
  `restart: unless-stopped`, sets `TZ`.
- **Makefile** targets: `help`, `setup` (`uv sync`), `run`, `test`, `lint`, `format`,
  `quality`, `docker-build`, `docker-up`, `docker-down`.
- **Tests** (pytest, written test-first):
  - `config` — required-var validation and defaults.
  - `HassClient` — mocked `requests`: success, non-200, not-found, unavailable, connection
    error, auth header, URL format, `is_reachable` cases, unit extraction.
  - `app` routes — `/` returns 200 and renders dashboard when reachable / offline when not;
    `/favicon.ico` returns 200.
  - `view` — view model shape, per-sensor error → `--`, unit passthrough.
- **Repo hygiene** — a `CLAUDE.md` capturing the conventions (env-var config, uv, Make-first,
  TDD, planning under `context/planning/`, no auto-commits), a `context/styling/formatting.md`
  style guide, and a `README.md`.

## Out of scope (YAGNI)

- Historical charts/graphs or trends.
- Authentication on the dashboard (LAN-only, trusted display).
- A configuration UI or multi-page navigation.
- Unit conversion (°C↔°F): the HA-native unit is displayed as-is.

## Code style

Follow `context/styling/formatting.md`:
- Classes `PascalCase`, constants `UPPER_SNAKE_CASE`, private attrs `_`-prefixed.
- Google-style docstrings on public methods (`Args:` / `Returns:`).
- 4-space indentation; ruff for lint + format (line length 120).
- CSS IDs/classes in `snake_case`; dark theme only; flexbox only (no grid/custom props).

---

# Fridge Dashboard — Implementation Plan

> **For agentic workers:** Use TDD (write the failing test first). Steps use checkbox
> (`- [ ]`) syntax for tracking. Run everything through `make`/`uv`.

**Goal:** Build a Flask server that renders a dark, Apple-widget-style fridge dashboard
(time, power, temperature, humidity) from Home Assistant sensors, packaged with uv + Docker.

**Architecture:** `config.py` (env vars) → `HassClient` (HA REST) → `dashboard/view.py`
(view model) → Flask `app.py` rendering Jinja2 templates. Meta-refresh + tiny ES5 clock.

**Tech Stack:** Python 3.11+, Flask, Jinja2 (bundled), requests, Gunicorn, uv, pytest, ruff,
Docker.

## Global Constraints

- Target browser is **Safari 9 (iOS 9)**: CSS **flexbox OK**, **no CSS Grid**, **no CSS
  custom properties**; **ES5 JavaScript only**.
- All configuration comes from **environment variables** (see config table above). No
  secrets in git.
- Dependencies managed by **uv**; `uv.lock` committed.
- **Make-first**: use `make` targets. **TDD**: failing test before implementation.
- Dark theme only. Units read from HA `unit_of_measurement`, never hardcoded.
- Code style per `context/styling/formatting.md` (PascalCase classes, UPPER_SNAKE_CASE
  constants, `_`-prefixed private attrs, Google-style docstrings, ruff line-length 120).
- **No auto-commits**: do not run git write commands unless the user asks.

---

### Task 1: Project scaffolding + configuration module

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `.env.example`, `config.py`, `__init__.py` files
- Test: `tests/test_config.py`, `tests/conftest.py`

**Interfaces:**
- Produces: `config.load_config() -> Config` where `Config` is a frozen dataclass with
  fields `hass_ip: str`, `hass_port: str`, `hass_token: str`, `entity_temperature: str`,
  `entity_humidity: str`, `entity_power: str`, `page_refresh_interval_seconds: int`,
  `server_port: int`. Raises `ConfigError` (subclass of `RuntimeError`) listing all missing
  required vars. Reads from `os.environ`.

- [ ] **Step 1:** Create `pyproject.toml` with `[project]` (name `fridge-dashboard`,
  requires-python `>=3.11`, deps `flask`, `requests`, `gunicorn`), dev dependency group
  (`pytest`, `ruff`), `[tool.pytest.ini_options]` (`testpaths=["tests"]`,
  `pythonpath=["."]`), and `[tool.ruff]` (`line-length=120`, lint select `E,F,I,W`).
- [ ] **Step 2:** Create `.gitignore` (`.venv`, `__pycache__`, `.env`, `*.pyc`,
  `.pytest_cache`, `.ruff_cache`) and `.env.example` documenting every variable.
- [ ] **Step 3:** Write failing tests in `tests/test_config.py`:

```python
import pytest
from config import load_config, ConfigError

REQUIRED = {
    "HASS_IP": "192.168.1.10",
    "HASS_PORT": "8123",
    "HASS_TOKEN": "tok",
    "ENTITY_TEMPERATURE": "sensor.t",
    "ENTITY_HUMIDITY": "sensor.h",
    "ENTITY_POWER": "sensor.p",
}

def test_loads_required_values(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)
    cfg = load_config()
    assert cfg.hass_ip == "192.168.1.10"
    assert cfg.entity_power == "sensor.p"

def test_defaults_applied(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("PAGE_REFRESH_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("SERVER_PORT", raising=False)
    cfg = load_config()
    assert cfg.page_refresh_interval_seconds == 60
    assert cfg.server_port == 6123

def test_missing_required_raises_listing_all(monkeypatch):
    for k in REQUIRED:
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(ConfigError) as exc:
        load_config()
    assert "HASS_IP" in str(exc.value)
    assert "ENTITY_POWER" in str(exc.value)
```

- [ ] **Step 4:** Run `make test` (or `uv run pytest tests/test_config.py -v`); expect FAIL
  (no `config` module).
- [ ] **Step 5:** Implement `config.py`:

```python
import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    hass_ip: str
    hass_port: str
    hass_token: str
    entity_temperature: str
    entity_humidity: str
    entity_power: str
    page_refresh_interval_seconds: int
    server_port: int


_REQUIRED = [
    "HASS_IP",
    "HASS_PORT",
    "HASS_TOKEN",
    "ENTITY_TEMPERATURE",
    "ENTITY_HUMIDITY",
    "ENTITY_POWER",
]


def load_config() -> Config:
    """
    Loads and validates dashboard configuration from environment variables.

    Returns:
      Config: The validated configuration.

    Raises:
      ConfigError: If any required environment variable is missing.
    """
    missing = [name for name in _REQUIRED if not os.environ.get(name)]
    if missing:
        raise ConfigError(f"Missing required environment variables: {', '.join(missing)}")

    return Config(
        hass_ip=os.environ["HASS_IP"],
        hass_port=os.environ["HASS_PORT"],
        hass_token=os.environ["HASS_TOKEN"],
        entity_temperature=os.environ["ENTITY_TEMPERATURE"],
        entity_humidity=os.environ["ENTITY_HUMIDITY"],
        entity_power=os.environ["ENTITY_POWER"],
        page_refresh_interval_seconds=int(os.environ.get("PAGE_REFRESH_INTERVAL_SECONDS", "60")),
        server_port=int(os.environ.get("SERVER_PORT", "6123")),
    )
```

- [ ] **Step 6:** Run `make test`; expect PASS. Run `make lint`.

---

### Task 2: Home Assistant REST client

**Files:**
- Create: `homeassistant/__init__.py`, `homeassistant/client.py`
- Test: `tests/test_client.py`

**Interfaces:**
- Consumes: `Config` from Task 1.
- Produces: `HassClient(config: Config)` with `get_state(entity_id: str) -> dict`
  returning `{"result": "OK", "state": str, "unit": str | None}` on success or
  `{"result": "err"}` on failure; `is_reachable() -> bool`.

- [ ] **Step 1:** Write failing tests in `tests/test_client.py` covering: successful state +
  unit extraction, non-200, `{"message": "Entity not found."}`, `state == "unavailable"`,
  `requests.ConnectionError`, Bearer auth header, URL format
  (`http://<ip>:<port>/api/states/<id>`), `is_reachable` true/false/timeout.

```python
from unittest.mock import MagicMock, patch
import requests
from config import Config
from homeassistant.client import HassClient

CFG = Config("192.168.1.1", "8123", "tok", "sensor.t", "sensor.h", "sensor.p", 60, 6123)


def _client():
    return HassClient(CFG)


@patch("homeassistant.client.requests.get")
def test_get_state_success_with_unit(mock_get):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"state": "4.2", "attributes": {"unit_of_measurement": "°C"}}
    mock_get.return_value = resp
    out = _client().get_state("sensor.t")
    assert out == {"result": "OK", "state": "4.2", "unit": "°C"}


@patch("homeassistant.client.requests.get")
def test_get_state_missing_unit_is_none(mock_get):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"state": "4.2", "attributes": {}}
    mock_get.return_value = resp
    assert _client().get_state("sensor.t")["unit"] is None


@patch("homeassistant.client.requests.get")
def test_get_state_non_200(mock_get):
    mock_get.return_value = MagicMock(status_code=500)
    assert _client().get_state("sensor.t") == {"result": "err"}


@patch("homeassistant.client.requests.get")
def test_get_state_not_found(mock_get):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"message": "Entity not found."}
    mock_get.return_value = resp
    assert _client().get_state("sensor.x")["result"] == "err"


@patch("homeassistant.client.requests.get")
def test_get_state_unavailable(mock_get):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"state": "unavailable"}
    mock_get.return_value = resp
    assert _client().get_state("sensor.t")["result"] == "err"


@patch("homeassistant.client.requests.get")
def test_get_state_connection_error(mock_get):
    mock_get.side_effect = requests.ConnectionError()
    assert _client().get_state("sensor.t")["result"] == "err"


@patch("homeassistant.client.requests.get")
def test_get_state_url_and_auth(mock_get):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"state": "on", "attributes": {}}
    mock_get.return_value = resp
    _client().get_state("sensor.my")
    assert mock_get.call_args[0][0] == "http://192.168.1.1:8123/api/states/sensor.my"
    assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer tok"


@patch("homeassistant.client.requests.get")
def test_is_reachable_true(mock_get):
    mock_get.return_value = MagicMock(status_code=200)
    assert _client().is_reachable() is True


@patch("homeassistant.client.requests.get")
def test_is_reachable_false_non_200(mock_get):
    mock_get.return_value = MagicMock(status_code=503)
    assert _client().is_reachable() is False


@patch("homeassistant.client.requests.get")
def test_is_reachable_false_on_timeout(mock_get):
    mock_get.side_effect = requests.Timeout()
    assert _client().is_reachable() is False
```

- [ ] **Step 2:** Run tests; expect FAIL.
- [ ] **Step 3:** Implement `homeassistant/client.py`:

```python
import requests

from config import Config
from utils.logger import logger


class HassClient:
    def __init__(self, config: Config):
        """
        Initializes the Home Assistant REST client.

        Args:
          config (Config): The validated dashboard configuration.
        """
        self._base = f"http://{config.hass_ip}:{config.hass_port}/api/"
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.hass_token}",
        }

    def is_reachable(self) -> bool:
        """
        Checks whether the Home Assistant API root responds with HTTP 200.

        Returns:
          bool: True if reachable, False otherwise.
        """
        try:
            response = requests.get(self._base, headers=self._headers, timeout=5)
            return response.status_code == 200
        except requests.RequestException as exc:
            logger.error(f"HA unreachable: {exc}")
            return False

    def get_state(self, entity_id: str) -> dict:
        """
        Fetches the state and unit of a Home Assistant entity.

        Args:
          entity_id (str): The entity ID to fetch.

        Returns:
          dict: {"result": "OK", "state": str, "unit": str | None} on success,
              otherwise {"result": "err"}.
        """
        try:
            response = requests.get(f"{self._base}states/{entity_id}", headers=self._headers, timeout=5)
        except requests.RequestException:
            logger.error(f"Connection failed for {entity_id}")
            return {"result": "err"}

        if response.status_code != 200:
            logger.error(f"HA returned {response.status_code} for {entity_id}")
            return {"result": "err"}

        payload = response.json()
        if payload.get("message") == "Entity not found.":
            logger.error(f"Entity not found: {entity_id}")
            return {"result": "err"}
        if payload.get("state") == "unavailable":
            logger.error(f"Entity unavailable: {entity_id}")
            return {"result": "err"}

        return {
            "result": "OK",
            "state": payload.get("state"),
            "unit": payload.get("attributes", {}).get("unit_of_measurement"),
        }
```

- [ ] **Step 4:** Add `utils/__init__.py` and `utils/logger.py` (same as reference: a module
  `logger` with a stream handler at DEBUG). Run tests; expect PASS. Run `make lint`.

---

### Task 3: Dashboard view model

**Files:**
- Create: `dashboard/__init__.py`, `dashboard/view.py`
- Test: `tests/test_view.py`

**Interfaces:**
- Consumes: `HassClient`, `Config`.
- Produces: `build_dashboard_model(client: HassClient, config: Config, now: datetime) ->
  dict` returning
  `{"time": "HH:MM", "refresh": int, "temperature": Reading, "humidity": Reading,
  "power": Reading}` where `Reading` is `{"value": str, "unit": str, "ok": bool}`.
  On a sensor error, `value == "--"`, `unit == ""`, `ok == False`.

- [ ] **Step 1:** Write failing tests in `tests/test_view.py`:

```python
from datetime import datetime
from unittest.mock import MagicMock
from config import Config
from dashboard.view import build_dashboard_model

CFG = Config("ip", "8123", "tok", "sensor.t", "sensor.h", "sensor.p", 30, 6123)


def test_model_maps_readings_and_units():
    client = MagicMock()
    client.get_state.side_effect = lambda eid: {
        "sensor.t": {"result": "OK", "state": "4.2", "unit": "°C"},
        "sensor.h": {"result": "OK", "state": "58", "unit": "%"},
        "sensor.p": {"result": "OK", "state": "120", "unit": "W"},
    }[eid]
    model = build_dashboard_model(client, CFG, datetime(2026, 1, 1, 12, 45))
    assert model["time"] == "12:45"
    assert model["refresh"] == 30
    assert model["temperature"] == {"value": "4.2", "unit": "°C", "ok": True}
    assert model["power"] == {"value": "120", "unit": "W", "ok": True}


def test_model_handles_sensor_error():
    client = MagicMock()
    client.get_state.return_value = {"result": "err"}
    model = build_dashboard_model(client, CFG, datetime(2026, 1, 1, 9, 5))
    assert model["time"] == "09:05"
    assert model["humidity"] == {"value": "--", "unit": "", "ok": False}
```

- [ ] **Step 2:** Run tests; expect FAIL.
- [ ] **Step 3:** Implement `dashboard/view.py`:

```python
from datetime import datetime

from config import Config
from homeassistant.client import HassClient


def _reading(client: HassClient, entity_id: str) -> dict:
    """
    Builds a single sensor reading dict, normalizing errors to a placeholder.

    Args:
      client (HassClient): The Home Assistant client.
      entity_id (str): The entity ID to read.

    Returns:
      dict: {"value": str, "unit": str, "ok": bool}.
    """
    state = client.get_state(entity_id)
    if state["result"] != "OK":
        return {"value": "--", "unit": "", "ok": False}
    return {"value": state["state"], "unit": state["unit"] or "", "ok": True}


def build_dashboard_model(client: HassClient, config: Config, now: datetime) -> dict:
    """
    Builds the view model rendered by the dashboard template.

    Args:
      client (HassClient): The Home Assistant client.
      config (Config): The validated configuration.
      now (datetime): The current time used for the server-rendered clock.

    Returns:
      dict: View model with time, refresh interval, and three readings.
    """
    return {
        "time": now.strftime("%H:%M"),
        "refresh": config.page_refresh_interval_seconds,
        "temperature": _reading(client, config.entity_temperature),
        "humidity": _reading(client, config.entity_humidity),
        "power": _reading(client, config.entity_power),
    }
```

- [ ] **Step 4:** Run tests; expect PASS. Run `make lint`.

---

### Task 4: Flask app, routes, and templates

**Files:**
- Create: `app.py`, `templates/dashboard.html`, `templates/offline.html`,
  `templates/_head.html`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `load_config`, `HassClient`, `build_dashboard_model`.
- Produces: Flask `app`; route `/` (dashboard or offline), `/favicon.ico`.

- [ ] **Step 1:** Write failing tests in `tests/test_app.py` using a fixture that injects a
  fake client and config, patching `app.get_client` / `app.CONFIG`:

```python
from unittest.mock import patch, MagicMock
import pytest
from config import Config

CFG = Config("ip", "8123", "tok", "sensor.t", "sensor.h", "sensor.p", 60, 6123)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("HASS_IP", "ip")
    monkeypatch.setenv("HASS_PORT", "8123")
    monkeypatch.setenv("HASS_TOKEN", "tok")
    monkeypatch.setenv("ENTITY_TEMPERATURE", "sensor.t")
    monkeypatch.setenv("ENTITY_HUMIDITY", "sensor.h")
    monkeypatch.setenv("ENTITY_POWER", "sensor.p")
    import importlib
    import app as app_module
    importlib.reload(app_module)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c, app_module


def test_dashboard_when_reachable(client):
    c, app_module = client
    fake = MagicMock()
    fake.is_reachable.return_value = True
    fake.get_state.return_value = {"result": "OK", "state": "4.2", "unit": "°C"}
    with patch.object(app_module, "_client", fake):
        resp = c.get("/")
    assert resp.status_code == 200
    assert b"4.2" in resp.data


def test_offline_when_unreachable(client):
    c, app_module = client
    fake = MagicMock()
    fake.is_reachable.return_value = False
    with patch.object(app_module, "_client", fake):
        resp = c.get("/")
    assert resp.status_code == 200
    assert b"Unreachable" in resp.data


def test_favicon(client):
    c, _ = client
    assert c.get("/favicon.ico").status_code == 200
```

- [ ] **Step 2:** Run tests; expect FAIL.
- [ ] **Step 3:** Implement `app.py`:

```python
from datetime import datetime

from flask import Flask, render_template

from config import load_config
from dashboard.view import build_dashboard_model
from homeassistant.client import HassClient

app = Flask(__name__)
CONFIG = load_config()
_client = HassClient(CONFIG)


@app.route("/")
def home():
    """
    Renders the dashboard, or an offline page when Home Assistant is unreachable.

    Returns:
      str: The rendered HTML page.
    """
    if not _client.is_reachable():
        return render_template("offline.html", refresh=CONFIG.page_refresh_interval_seconds,
                               time=datetime.now().strftime("%H:%M"))
    model = build_dashboard_model(_client, CONFIG, datetime.now())
    return render_template("dashboard.html", **model)


@app.route("/favicon.ico")
def favicon():
    """
    Serves the favicon.

    Returns:
      Response: The favicon file.
    """
    return app.send_static_file("assets/favicon.ico")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=CONFIG.server_port, debug=True)
```

- [ ] **Step 4:** Create `templates/_head.html` (shared `<head>`: charset, viewport,
  `<meta http-equiv="refresh" content="{{ refresh }}">`, stylesheet link, title), and
  `templates/dashboard.html` and `templates/offline.html` extending/ including it. The
  dashboard renders the 3-column `<table>` (left: clock `<span id="clock">{{ time }}</span>`
  over power; center: thermometer SVG + temperature; right: droplet SVG + humidity), and
  includes `clock.js`. Offline shows a centered "Home Assistant is Unreachable" card + time.
- [ ] **Step 5:** Run tests; expect PASS. Run `make lint`.

---

### Task 5: Static assets — CSS, clock JS, SVG icons, favicon

**Files:**
- Create: `static/css/styles.css`, `static/js/clock.js`,
  `static/assets/thermometer.svg`, `static/assets/droplet.svg`,
  `static/assets/favicon.ico`

- [ ] **Step 1:** Write `static/css/styles.css` — dark theme, `html,body{height:100%;margin:0}`,
  full-screen `table{width:100%;height:100%}`, three equal columns, inner `.card` divs with
  `border-radius`, `box-shadow`, dark-grey background; left column split via a flex column
  into `.clock_half` / `.power_half`; big `font-size` for values; `.clock` bold monospace.
  **Flexbox only — no grid, no CSS custom properties.**
- [ ] **Step 2:** Write `static/js/clock.js` (ES5):

```javascript
(function () {
  function pad(n) { return n < 10 ? "0" + n : "" + n; }
  function tick() {
    var el = document.getElementById("clock");
    if (!el) return;
    var d = new Date();
    el.firstChild ? (el.firstChild.nodeValue = pad(d.getHours()) + ":" + pad(d.getMinutes()))
                  : (el.innerHTML = pad(d.getHours()) + ":" + pad(d.getMinutes()));
  }
  tick();
  setInterval(tick, 1000);
})();
```

- [ ] **Step 3:** Create simple single-path `thermometer.svg` and `droplet.svg` using
  `fill="currentColor"` so CSS controls color; add a small `favicon.ico`.
- [ ] **Step 4:** Manually verify rendering by running `make run` and opening the page; check
  layout matches the design mock. Run `make test` and `make lint`.

---

### Task 6: Packaging — uv, Dockerfile, docker-compose, Makefile

**Files:**
- Create: `Dockerfile`, `docker-compose.yaml`, `Makefile`; ensure `uv.lock` committed

- [ ] **Step 1:** `Makefile` targets: `help` (default), `setup` (`uv sync`), `run`
  (`uv run python app.py`), `test` (`uv run pytest tests/ -v`), `lint`
  (`uv run ruff check . && uv run ruff format --check .`), `format`
  (`uv run ruff check --fix . && uv run ruff format .`), `quality`, `docker-build`,
  `docker-up`, `docker-down`.
- [ ] **Step 2:** `Dockerfile` (uv-based):

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev
EXPOSE 6123
CMD ["sh", "-c", "uv run gunicorn -w 2 -b 0.0.0.0:${SERVER_PORT:-6123} -t 0 app:app"]
```

- [ ] **Step 3:** `docker-compose.yaml`:

```yaml
services:
  fridge_dashboard:
    build: .
    container_name: fridge_dashboard
    restart: unless-stopped
    env_file: .env
    environment:
      - TZ=Europe/Rome
    ports:
      - "${SERVER_PORT:-6123}:${SERVER_PORT:-6123}"
```

- [ ] **Step 4:** Run `make setup` then `make test` to confirm the uv workflow works end to
  end. Run `make docker-build` if Docker is available.

---

### Task 7: Documentation & repo hygiene

**Files:**
- Create: `README.md`, `CLAUDE.md`, `context/styling/formatting.md`

- [ ] **Step 1:** `README.md` — what it is, the env vars, `make setup`/`run`/`test`, Docker
  deployment, and how to point the iPad at `http://<host>:<SERVER_PORT>/`.
- [ ] **Step 2:** `CLAUDE.md` — project overview, commands, architecture, the Safari-9 design
  constraints, env-var config note, uv + Make-first + TDD + no-auto-commit conventions, and
  the `context/planning/` workflow.
- [ ] **Step 3:** `context/styling/formatting.md` — Python naming/docstrings/indentation,
  CSS conventions (snake_case, dark theme, flexbox only), template conventions.
- [ ] **Step 4:** Final full run: `make test` (all pass) and `make lint` (clean).

