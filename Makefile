SHELL := /bin/bash

.PHONY: help install test lint format typecheck check build clean

help: ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?##"};{printf "  %-12s %s\n",$$1,$$2}'

install: ## sync python deps + install pre-commit hooks
	uv sync --all-extras --group dev
	uv run pre-commit install

test: ## run pytest
	uv run pytest

lint: ## ruff check + format-check
	uvx ruff check .
	uvx ruff format --check .

format: ## ruff format + autofix
	uvx ruff format .
	uvx ruff check --fix .

typecheck: ## ty check
	uvx ty check .

check: lint typecheck test ## everything CI runs

build: ## build wheel + sdist
	uv build

clean: ## wipe build artifacts
	rm -rf dist build *.egg-info
