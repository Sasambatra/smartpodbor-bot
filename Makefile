PYTHON ?= .venv/bin/python

.PHONY: setup dev run demo check test lint format preview build

setup:
	./setup.sh

dev: setup
	$(PYTHON) -m pip install -r requirements-dev.lock

run:
	$(PYTHON) -m smartphone_bot

demo:
	$(PYTHON) -m smartphone_bot --demo --example

lint:
	$(PYTHON) -m ruff check smartphone_bot tests scripts
	$(PYTHON) -m ruff format --check smartphone_bot tests scripts

format:
	$(PYTHON) -m ruff check --fix smartphone_bot tests scripts
	$(PYTHON) -m ruff format smartphone_bot tests scripts

test:
	$(PYTHON) -m pytest --cov --cov-report=term-missing --cov-report=xml -q

preview:
	$(PYTHON) scripts/export_demo.py

check: lint test
	$(PYTHON) -m smartphone_bot --check
	$(PYTHON) scripts/export_demo.py --check

build:
	$(PYTHON) -m build
	$(PYTHON) scripts/check_distribution.py dist
