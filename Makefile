# SERVER_REPO: Tessera server checkout that owns openapi.json.
# Override: make sync-spec SERVER_REPO=/path/to/ai-memory
SERVER_REPO ?= ../ai-memory

.PHONY: sync-spec generate lint typecheck test

sync-spec:
	cp $(SERVER_REPO)/openapi.json openapi.json

generate:
	uv run python scripts/generate_models.py

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy

test:
	uv run pytest -q
