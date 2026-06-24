import requests

from config import Config
from utils.logger import logger

# Home Assistant state strings that mean "no usable reading".
_UNUSABLE_STATES = {None, "unavailable", "unknown"}


class HassClient:
    """Reads entity state from a Home Assistant instance over its REST API."""

    def __init__(self, config: Config):
        """
        Args:
          config (Config): The validated dashboard configuration.
        """
        self._base = f"http://{config.hass_ip}:{config.hass_port}/api/"
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.hass_token}",
        }

    def _get(self, path: str):
        """
        Args:
          path (str): The path appended to the API base (e.g. "states/sensor.x").

        Returns:
          requests.Response | None: The response, or None if the request failed.
        """
        try:
            return requests.get(f"{self._base}{path}", headers=self._headers, timeout=5)
        except requests.RequestException as exc:
            logger.error(f"HA request failed for '{path}': {exc}")
            return None

    def is_reachable(self) -> bool:
        """
        Returns:
          bool: True if reachable, False otherwise.
        """
        response = self._get("")
        return response is not None and response.status_code == 200

    def get_state(self, entity_id: str) -> dict:
        """
        Args:
          entity_id (str): The entity ID to fetch.

        Returns:
          dict: {"result": "OK", "state": str, "unit": str | None} on success,
              otherwise {"result": "err"}.
        """
        response = self._get(f"states/{entity_id}")

        if response is None:
            return {"result": "err"}

        if response.status_code != 200:
            logger.error(f"HA returned {response.status_code} for {entity_id}")
            return {"result": "err"}

        try:
            payload = response.json()
        except ValueError:
            logger.error(f"HA returned a non-JSON body for {entity_id}")
            return {"result": "err"}

        if payload.get("message") == "Entity not found.":
            logger.error(f"Entity not found: {entity_id}")
            return {"result": "err"}
        if payload.get("state") in _UNUSABLE_STATES:
            logger.error(f"Entity has no usable state: {entity_id}")
            return {"result": "err"}

        return {
            "result": "OK",
            "state": payload.get("state"),
            "unit": payload.get("attributes", {}).get("unit_of_measurement"),
        }
