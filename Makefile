# Makefile for easy development workflows.
# See docs/development.md for docs.
# Note GitHub Actions call uv directly, not this Makefile.

.DEFAULT_GOAL := default

UV ?= UV_NO_CONFIG=1 uv
EXCLUDE_NEWER_DATE := $(shell date -u -v-14d +%Y-%m-%d 2>/dev/null || date -u -d '14 days ago' +%Y-%m-%d)

.PHONY: default install lint lint-check test audit upgrade sync-frozen build clean

default: install lint test audit

install:
	$(UV) sync --all-extras

lint:
	$(UV) run python devtools/lint.py

# Check-only lint, matching CI (does not modify files).
lint-check:
	$(UV) run python devtools/lint.py --check

test:
	$(UV) run pytest

audit:
	$(UV) run pip-audit

upgrade:
	$(UV) lock --upgrade --exclude-newer $(EXCLUDE_NEWER_DATE)
	$(UV) sync --all-extras --dev

sync-frozen:
	$(UV) sync --frozen --all-extras

build:
	$(UV) build

clean:
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .pytest_cache/
	-rm -rf .mypy_cache/
	-rm -rf .venv/
	-find . -type d -name "__pycache__" -exec rm -rf {} +
