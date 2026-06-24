.PHONY: help setup run debug test lint format quality docker-build docker-up docker-down

.DEFAULT_GOAL := help

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  setup          Create the uv environment and install all dependencies"
	@echo "  run            Run the Flask dev server"
	@echo "  debug          Launch the app in the terminal, loading .env if present"
	@echo "  test           Run the full test suite"
	@echo "  lint           Check linting + formatting"
	@echo "  format         Auto-fix lint issues and format"
	@echo "  quality        Run lint then format"
	@echo "  docker-build   Build the Docker image"
	@echo "  docker-up      Build and run with Docker Compose"
	@echo "  docker-down    Stop Docker containers"

setup:
	uv sync

run:
	uv run python app.py

debug:
	@if [ -f .env ]; then set -a; . ./.env; set +a; fi; uv run python app.py

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

quality:
	$(MAKE) lint
	$(MAKE) format

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
