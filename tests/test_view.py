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
    assert model["theme"] == "dark"
    assert model["temperature"] == {"value": "4.2", "unit": "°C", "ok": True}
    assert model["humidity"] == {"value": "58", "unit": "%", "ok": True}
    assert model["power"] == {"value": "120", "unit": "W", "ok": True}


def test_model_handles_sensor_error():
    client = MagicMock()
    client.get_state.return_value = {"result": "err"}
    model = build_dashboard_model(client, CFG, datetime(2026, 1, 1, 9, 5))
    assert model["time"] == "09:05"
    assert model["humidity"] == {"value": "--", "unit": "", "ok": False}


def test_model_handles_missing_unit():
    client = MagicMock()
    client.get_state.return_value = {"result": "OK", "state": "7", "unit": None}
    model = build_dashboard_model(client, CFG, datetime(2026, 1, 1, 0, 0))
    assert model["temperature"] == {"value": "7", "unit": "", "ok": True}


def test_model_power_none_when_not_configured():
    client = MagicMock()
    client.get_state.return_value = {"result": "OK", "state": "1", "unit": "W"}
    cfg = Config("ip", "8123", "tok", "sensor.t", "sensor.h", "", 30, 6123)
    model = build_dashboard_model(client, cfg, datetime(2026, 1, 1, 0, 0))
    assert model["power"] is None
