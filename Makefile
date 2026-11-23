PY ?= python3

.PHONY: install lint test test-unit test-integration test-e2e privacy ci serve-fixtures validate-map next hooks

install:
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check .

test:
	$(PY) -m pytest -q

# Fast, no servers or subprocesses. Runs on every PR.
test-unit:
	$(PY) -m pytest -q -m "not integration and not e2e"

# Real local components together: fixture site, sqlite, the CLI as a subprocess.
test-integration:
	$(PY) -m pytest -q -m integration

# Whole workflows from the outside. Playwright joins here when web/ exists.
test-e2e:
	$(PY) -m pytest -q -m e2e

privacy:
	$(PY) -m pytest -q -m privacy

# One command, same on a clean clone, locally and in CI.
ci: lint test-unit test-integration test-e2e privacy validate-map

serve-fixtures:
	$(PY) fixtures/serve.py

validate-map:
	$(PY) tools/issue_map.py validate

next:
	$(PY) tools/issue_map.py next

hooks:
	git config core.hooksPath tools/hooks
	@echo "commit-msg hook installed: commits get the project owner as co-author"
