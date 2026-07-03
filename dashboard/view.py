from datetime import datetime

from config import Config
from homeassistant.client import HassClient

# Fridge-safe temperature band (°C) and the icon colors it maps to.
_TEMP_OK_LOW = 1.0
_TEMP_OK_HIGH = 4.0
_COLOR_OK = "#34c759"  # Apple system green
_COLOR_ALERT = "#ff3b30"  # Apple system red


def _temperature_color(reading: dict) -> str:
    """
    Picks the thermometer color for a temperature reading.

    Args:
      reading (dict): A reading dict from `_reading`.

    Returns:
      str: Green hex when 1 <= °C <= 4, red hex otherwise (including
          unreadable values).
    """
    try:
        temp = float(reading["value"])
    except (TypeError, ValueError):
        return _COLOR_ALERT
    return _COLOR_OK if _TEMP_OK_LOW <= temp <= _TEMP_OK_HIGH else _COLOR_ALERT


def _trend(client: HassClient, entity_id: str) -> str | None:
    """
    Reads a derivative (rate-of-change) sensor and reduces it to a trend.

    Args:
      client (HassClient): The Home Assistant client.
      entity_id (str): The derivative entity ID, or "" when not configured.

    Returns:
      str | None: "up" (>0), "down" (<0), or "stable" (==0). None when the
          entity is not configured, unreadable, or non-numeric — the arrow is
          then omitted and the UI looks as it does without the feature.
    """
    if not entity_id:
        return None

    state = client.get_state(entity_id)
    if state["result"] != "OK":
        return None

    try:
        rate = float(state["state"])
    except (TypeError, ValueError):
        return None

    if rate > 0:
        return "up"
    if rate < 0:
        return "down"
    return "stable"


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
      dict: View model with time, refresh interval, and readings. "power" is
          None when no power entity is configured (the clock then fills the
          left column).
    """
    temperature = _reading(client, config.entity_temperature)
    temperature["color"] = _temperature_color(temperature)
    temperature["trend"] = _trend(client, config.entity_temperature_derivative)

    humidity = _reading(client, config.entity_humidity)
    humidity["trend"] = _trend(client, config.entity_humidity_derivative)

    return {
        "time": now.strftime("%H:%M"),
        "refresh": config.page_refresh_interval_seconds,
        "theme": config.theme,
        "temperature": temperature,
        "humidity": humidity,
        "power": _reading(client, config.entity_power) if config.entity_power else None,
    }
