.PHONY: sync sync-api sync-web-search-mcp sync-google-mcp

# Rebuild the api and MCP images. Each Dockerfile runs
# `uv sync --locked` with dev dependencies disabled.

sync:
	docker compose build api web_search_mcp google_mcp

sync-api:
	docker compose build api

sync-web-search-mcp:
	docker compose build web_search_mcp

sync-google-mcp:
	docker compose build google_mcp
