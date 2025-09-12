.PHONY: help install lint format type-check test ci clean

help:  ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync --dev

lint:  ## Run ruff linting
	uv run ruff check src/ tests/

format:  ## Run ruff formatting
	uv run ruff format src/ tests/

format-check:  ## Check ruff formatting without making changes
	uv run ruff format --check src/ tests/

type-check:  ## Run mypy type checking
	uv run mypy src/

test:  ## Run fast tests (default - excludes slow tests)
	uv run pytest

test-fast:  ## Run fast tests only (alias for test)
	uv run pytest -m "not slow"

test-all:  ## Run all tests including slow ones
	uv run pytest -m ""

test-slow:  ## Run only slow tests
	uv run pytest -m "slow"

test-integration:  ## Run integration tests only
	uv run pytest -m "integration"

test-cov:  ## Run fast tests with coverage
	uv run pytest --cov=hydra_poster --cov-report=term-missing --cov-report=html --cov-fail-under=90

test-cov-all:  ## Run all tests with coverage
	uv run pytest -m "" --cov=hydra_poster --cov-report=term-missing --cov-report=html --cov-fail-under=90

ci:  ## Run all CI checks (lint, format-check, type-check, test)
	@echo "Running all CI checks..."
	@$(MAKE) lint
	@$(MAKE) format-check
	@$(MAKE) type-check
	@$(MAKE) test
	@echo "✅ All CI checks passed!"

clean:  ## Clean up cache files and build artifacts
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf src/*.egg-info/
	rm -rf dist/
	rm -rf build/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build the package
	uv build

dev:  ## Install package in development mode
	uv sync --dev