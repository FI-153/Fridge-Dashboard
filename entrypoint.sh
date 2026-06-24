#!/bin/sh
# Container entrypoint: launch the dashboard with Gunicorn, binding the
# configurable dashboard port (SERVER_PORT, default 6123). `exec` replaces the
# shell so Gunicorn becomes PID 1 and receives stop signals directly.
set -e

exec uv run gunicorn \
  --workers 2 \
  --bind "0.0.0.0:${SERVER_PORT:-6123}" \
  --timeout 0 \
  app:app
