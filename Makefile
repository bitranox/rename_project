.PHONY: help install dev test lint format typecheck clean all

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

dev:  ## Install the package with dev dependencies
	pip install -e ".[dev]"

test:  ## Run tests with pytest
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=rename_project --cov-report=term-missing --cov-report=html

lint:  ## Run ruff linter
	ruff check src tests

format:  ## Format code with ruff
	ruff format src tests
	ruff check --fix src tests

typecheck:  ## Run pyright type checker
	pyright

clean:  ## Remove build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

all: lint typecheck test  ## Run lint, typecheck, and test
