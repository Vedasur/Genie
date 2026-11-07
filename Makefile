.PHONY: sync sync-api sync-mcp

# Rebuild the api and mcp images. Dockerfile-api and Dockerfile-mcp each run
# `uv sync --locked` with dev dependencies disabled.

sync:
	docker compose build api mcp

sync-api:
	docker compose build api

sync-mcp:
	docker compose build mcp
