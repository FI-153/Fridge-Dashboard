#!/bin/sh
# Container entrypoint: launch the dashboard with Gunicorn, binding the
# configurable dashboard port (SERVER_PORT, default 6123). `exec` replaces the
# shell so Gunicorn becomes PID 1 and receives stop signals directly.
set -e

# Home Assistant add-on: the Configuration UI writes the options to
# /data/options.json. Map them to the env vars the app already reads (keys
# upper-cased: entity_temperature -> ENTITY_TEMPERATURE). A no-op for a plain
# `docker run`, where the file is absent.
# ponytail: stdlib json + shlex via the image's python; no jq/bashio needed.
if [ -f /data/options.json ]; then
  eval "$(python3 -c '
import json, shlex
for key, value in json.load(open("/data/options.json")).items():
    print(f"export {key.upper()}={shlex.quote(str(value))}")
')"
fi

# Home Assistant add-on with Supervisor API access (homeassistant_api: true):
# reach Core through the Supervisor proxy using the injected token, so no host,
# port, or long-lived token needs to be configured.
if [ -n "${SUPERVISOR_TOKEN:-}" ]; then
  export HASS_URL="http://supervisor/core/api/"
  export HASS_TOKEN="${SUPERVISOR_TOKEN}"
fi

exec uv run gunicorn \
  --workers 2 \
  --bind "0.0.0.0:${SERVER_PORT:-6123}" \
  --timeout 0 \
  app:app
