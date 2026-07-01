import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    """Validated dashboard configuration loaded from environment variables."""

    hass_ip: str
    hass_port: str
    hass_token: str
    entity_temperature: str
    entity_humidity: str
    entity_power: str
    page_refresh_interval_seconds: int
    server_port: int
    # Full API base URL (".../api/"). When set (e.g. the Home Assistant add-on
    # points it at the Supervisor proxy) it replaces hass_ip/hass_port.
    hass_url: str = ""
    # Color theme: "dark" (default) or "light".
    theme: str = "dark"


_REQUIRED = [
    "HASS_TOKEN",
    "ENTITY_TEMPERATURE",
    "ENTITY_HUMIDITY",
    "ENTITY_POWER",
]


def _positive_int_env(name: str, default: int) -> int:
    """
    Reads a positive integer from the environment, applying a default.

    Args:
      name (str): The environment variable name.
      default (int): The value used when the variable is unset or blank.

    Returns:
      int: The parsed, strictly-positive integer.

    Raises:
      ConfigError: If the value is not an integer or is not greater than zero.
    """
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default

    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from None

    if value <= 0:
        raise ConfigError(f"{name} must be a positive integer, got {value}")

    return value


def load_config() -> Config:
    """
    Returns:
      Config: The validated configuration.

    Raises:
      ConfigError: If a required variable is missing or an optional numeric
          variable is not a positive integer.
    """
    hass_url = os.environ.get("HASS_URL", "")
    theme = "light" if os.environ.get("THEME", "dark").strip().lower() == "light" else "dark"
    # Without an explicit API URL, it is built from host + port, so require those.
    required = _REQUIRED if hass_url else ["HASS_IP", "HASS_PORT", *_REQUIRED]

    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ConfigError(f"Missing required environment variables: {', '.join(missing)}")

    return Config(
        hass_ip=os.environ.get("HASS_IP", ""),
        hass_port=os.environ.get("HASS_PORT", ""),
        hass_token=os.environ["HASS_TOKEN"],
        entity_temperature=os.environ["ENTITY_TEMPERATURE"],
        entity_humidity=os.environ["ENTITY_HUMIDITY"],
        entity_power=os.environ["ENTITY_POWER"],
        page_refresh_interval_seconds=_positive_int_env("PAGE_REFRESH_INTERVAL_SECONDS", 60),
        server_port=_positive_int_env("SERVER_PORT", 6123),
        hass_url=hass_url,
        theme=theme,
    )
