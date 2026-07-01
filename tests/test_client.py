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
    assert _client().get_state("sensor.t") == {"result": "OK", "state": "4.2", "unit": "°C"}


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
def test_get_state_unknown_is_err(mock_get):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"state": "unknown", "attributes": {"unit_of_measurement": "°C"}}
    mock_get.return_value = resp
    assert _client().get_state("sensor.t")["result"] == "err"


@patch("homeassistant.client.requests.get")
def test_get_state_none_state_is_err(mock_get):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"state": None, "attributes": {}}
    mock_get.return_value = resp
    assert _client().get_state("sensor.t")["result"] == "err"


@patch("homeassistant.client.requests.get")
def test_get_state_invalid_json_is_err(mock_get):
    resp = MagicMock(status_code=200)
    resp.json.side_effect = ValueError("no json could be decoded")
    mock_get.return_value = resp
    assert _client().get_state("sensor.t") == {"result": "err"}


@patch("homeassistant.client.requests.get")
def test_get_state_zero_value_is_ok(mock_get):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"state": "0", "attributes": {"unit_of_measurement": "W"}}
    mock_get.return_value = resp
    assert _client().get_state("sensor.p") == {"result": "OK", "state": "0", "unit": "W"}


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
def test_get_state_uses_hass_url_base(mock_get):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"state": "1", "attributes": {}}
    mock_get.return_value = resp
    cfg = Config("", "", "tok", "sensor.t", "sensor.h", "sensor.p", 60, 6123, "http://supervisor/core/api/")
    HassClient(cfg).get_state("sensor.x")
    assert mock_get.call_args[0][0] == "http://supervisor/core/api/states/sensor.x"


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
