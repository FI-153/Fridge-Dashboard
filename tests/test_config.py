import pytest

from config import ConfigError, load_config

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
    assert cfg.hass_port == "8123"
    assert cfg.hass_token == "tok"
    assert cfg.entity_temperature == "sensor.t"
    assert cfg.entity_humidity == "sensor.h"
    assert cfg.entity_power == "sensor.p"


def test_defaults_applied(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("PAGE_REFRESH_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("SERVER_PORT", raising=False)
    cfg = load_config()
    assert cfg.page_refresh_interval_seconds == 60
    assert cfg.server_port == 6123


def test_overrides_optional_values(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("PAGE_REFRESH_INTERVAL_SECONDS", "30")
    monkeypatch.setenv("SERVER_PORT", "9000")
    cfg = load_config()
    assert cfg.page_refresh_interval_seconds == 30
    assert cfg.server_port == 9000


def test_non_integer_optional_raises_config_error(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("SERVER_PORT", "not-a-number")
    with pytest.raises(ConfigError) as exc:
        load_config()
    assert "SERVER_PORT" in str(exc.value)


def test_zero_refresh_interval_raises_config_error(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("PAGE_REFRESH_INTERVAL_SECONDS", "0")
    with pytest.raises(ConfigError) as exc:
        load_config()
    assert "PAGE_REFRESH_INTERVAL_SECONDS" in str(exc.value)


def test_blank_optional_falls_back_to_default(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("SERVER_PORT", "")
    cfg = load_config()
    assert cfg.server_port == 6123


def test_hass_url_replaces_ip_port(monkeypatch):
    monkeypatch.delenv("HASS_IP", raising=False)
    monkeypatch.delenv("HASS_PORT", raising=False)
    monkeypatch.setenv("HASS_TOKEN", "tok")
    monkeypatch.setenv("HASS_URL", "http://supervisor/core/api/")
    monkeypatch.setenv("ENTITY_TEMPERATURE", "sensor.t")
    monkeypatch.setenv("ENTITY_HUMIDITY", "sensor.h")
    monkeypatch.setenv("ENTITY_POWER", "sensor.p")
    cfg = load_config()
    assert cfg.hass_url == "http://supervisor/core/api/"


def test_theme_defaults_dark(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("THEME", raising=False)
    assert load_config().theme == "dark"


def test_theme_light(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("THEME", "Light")
    assert load_config().theme == "light"


def test_theme_invalid_coerces_dark(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("THEME", "banana")
    assert load_config().theme == "dark"


def test_missing_required_raises_listing_all(monkeypatch):
    for k in REQUIRED:
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(ConfigError) as exc:
        load_config()
    message = str(exc.value)
    assert "HASS_IP" in message
    assert "ENTITY_POWER" in message
