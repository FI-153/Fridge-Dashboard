FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Install dependencies first (better layer caching), without the project itself.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the application and sync the project into the environment.
COPY . .
RUN uv sync --frozen --no-dev && chmod +x /app/entrypoint.sh

# Default dashboard port (informational; the actual port follows SERVER_PORT).
EXPOSE 6123

# Home Assistant add-on labels (Supervisor passes BUILD_VERSION when it builds
# the add-on; harmless/empty for a plain docker build).
ARG BUILD_VERSION
LABEL io.hass.type="addon" io.hass.version="${BUILD_VERSION}"

# The launch command lives in entrypoint.sh so it can be read/overridden easily.
ENTRYPOINT ["/app/entrypoint.sh"]
