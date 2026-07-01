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
        "theme": config.theme,
        "temperature": _reading(client, config.entity_temperature),
        "humidity": _reading(client, config.entity_humidity),
        "power": _reading(client, config.entity_power),
    }
