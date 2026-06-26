import importlib
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("HASS_IP", "ip")
    monkeypatch.setenv("HASS_PORT", "8123")
    monkeypatch.setenv("HASS_TOKEN", "tok")
    monkeypatch.setenv("ENTITY_TEMPERATURE", "sensor.t")
    monkeypatch.setenv("ENTITY_HUMIDITY", "sensor.h")
    monkeypatch.setenv("ENTITY_POWER", "sensor.p")
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


def test_dashboard_includes_refresh_meta(client):
    c, app_module = client
    fake = MagicMock()
    fake.is_reachable.return_value = True
    fake.get_state.return_value = {"result": "OK", "state": "1", "unit": "W"}
    with patch.object(app_module, "_client", fake):
        resp = c.get("/")
    assert b'http-equiv="refresh"' in resp.data


def test_health_returns_200(client):
    c, _ = client
    resp = c.get("/health")
    assert resp.status_code == 200


def test_health_does_not_depend_on_home_assistant(client):
    c, app_module = client
    fake = MagicMock()
    fake.is_reachable.return_value = False
    with patch.object(app_module, "_client", fake):
        resp = c.get("/health")
    assert resp.status_code == 200
    fake.is_reachable.assert_not_called()
