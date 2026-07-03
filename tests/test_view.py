from datetime import datetime
from unittest.mock import MagicMock

from config import Config
from dashboard.view import _COLOR_ALERT, _COLOR_OK, build_dashboard_model

CFG = Config("ip", "8123", "tok", "sensor.t", "sensor.h", "sensor.p", 30, 6123)


def _model_with_temp(value):
    client = MagicMock()
    client.get_state.side_effect = lambda eid: (
        {"result": "OK", "state": value, "unit": "°C"}
        if eid == "sensor.t"
        else {"result": "OK", "state": "50", "unit": "%"}
    )
    return build_dashboard_model(client, CFG, datetime(2026, 1, 1, 0, 0))


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
    assert model["temperature"] == {"value": "4.2", "unit": "°C", "ok": True, "color": _COLOR_ALERT, "trend": None}
    assert model["humidity"] == {"value": "58", "unit": "%", "ok": True, "trend": None}
    assert model["power"] == {"value": "120", "unit": "W", "ok": True}


def test_temperature_color_green_in_range():
    for value in ["1", "2.5", "4"]:  # inclusive bounds
        assert _model_with_temp(value)["temperature"]["color"] == _COLOR_OK


def test_temperature_color_red_out_of_range():
    for value in ["0.9", "4.1", "-3", "12"]:
        assert _model_with_temp(value)["temperature"]["color"] == _COLOR_ALERT


def test_temperature_color_red_when_unreadable():
    client = MagicMock()
    client.get_state.return_value = {"result": "err"}
    model = build_dashboard_model(client, CFG, datetime(2026, 1, 1, 0, 0))
    assert model["temperature"]["color"] == _COLOR_ALERT


def test_model_handles_sensor_error():
    client = MagicMock()
    client.get_state.return_value = {"result": "err"}
    model = build_dashboard_model(client, CFG, datetime(2026, 1, 1, 9, 5))
    assert model["time"] == "09:05"
    assert model["humidity"] == {"value": "--", "unit": "", "ok": False, "trend": None}


def test_model_handles_missing_unit():
    client = MagicMock()
    client.get_state.return_value = {"result": "OK", "state": "7", "unit": None}
    model = build_dashboard_model(client, CFG, datetime(2026, 1, 1, 0, 0))
    assert model["temperature"] == {"value": "7", "unit": "", "ok": True, "color": _COLOR_ALERT, "trend": None}


def _model_with_derivative(temp_rate_state):
    """Model where the temperature derivative sensor returns `temp_rate_state`."""
    client = MagicMock()
    client.get_state.side_effect = lambda eid: {
        "sensor.t": {"result": "OK", "state": "4.2", "unit": "°C"},
        "sensor.h": {"result": "OK", "state": "50", "unit": "%"},
        "sensor.t_rate": temp_rate_state,
    }[eid]
    cfg = Config(
        "ip", "8123", "tok", "sensor.t", "sensor.h", "", 30, 6123, entity_temperature_derivative="sensor.t_rate"
    )
    return build_dashboard_model(client, cfg, datetime(2026, 1, 1, 0, 0))


def test_trend_none_when_derivative_not_configured():
    assert _model_with_temp("4.2")["temperature"]["trend"] is None


def test_trend_up_when_positive():
    model = _model_with_derivative({"result": "OK", "state": "0.5", "unit": "°C/min"})
    assert model["temperature"]["trend"] == "up"


def test_trend_down_when_negative():
    model = _model_with_derivative({"result": "OK", "state": "-0.3", "unit": "°C/min"})
    assert model["temperature"]["trend"] == "down"


def test_trend_stable_when_zero():
    for zero in ["0", "0.0"]:
        model = _model_with_derivative({"result": "OK", "state": zero, "unit": "°C/min"})
        assert model["temperature"]["trend"] == "stable"


def test_trend_none_when_derivative_unreadable():
    model = _model_with_derivative({"result": "err"})
    assert model["temperature"]["trend"] is None


def test_trend_none_when_derivative_non_numeric():
    model = _model_with_derivative({"result": "OK", "state": "unavailable", "unit": ""})
    assert model["temperature"]["trend"] is None


def test_model_power_none_when_not_configured():
    client = MagicMock()
    client.get_state.return_value = {"result": "OK", "state": "1", "unit": "W"}
    cfg = Config("ip", "8123", "tok", "sensor.t", "sensor.h", "", 30, 6123)
    model = build_dashboard_model(client, cfg, datetime(2026, 1, 1, 0, 0))
    assert model["power"] is None
