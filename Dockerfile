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

# Home Assistant add-on labels. CI passes BUILD_VERSION/BUILD_ARCH per image;
# empty (harmless) for a plain docker build.
ARG BUILD_VERSION
ARG BUILD_ARCH
LABEL io.hass.type="addon" io.hass.version="${BUILD_VERSION}" io.hass.arch="${BUILD_ARCH}"

# The launch command lives in entrypoint.sh so it can be read/overridden easily.
ENTRYPOINT ["/app/entrypoint.sh"]
