.PHONY: help install install-dev test test-cov lint format type-check clean build upload docs

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package
	pip install -e .

install-dev:  ## Install package with development dependencies
	pip install -e ".[dev]"
	pre-commit install

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage report
	pytest --cov=emutrader --cov-report=html --cov-report=term

lint:  ## Run code linting
	flake8 emutrader tests

format:  ## Format code with black
	black emutrader tests

type-check:  ## Run type checking
	mypy emutrader

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build package
	python -m build

upload:  ## Upload to PyPI (requires API token)
	python -m twine upload dist/*

docs:  ## Generate documentation
	cd docs && make html

quality:  ## Run all quality checks
	$(MAKE) format
	$(MAKE) lint  
	$(MAKE) type-check
	$(MAKE) test-cov