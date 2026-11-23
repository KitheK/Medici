PY ?= python3

.PHONY: install lint test privacy ci serve-fixtures validate-map next hooks

install:
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check .

test:
	$(PY) -m pytest -q

privacy:
	$(PY) -m pytest -q -m privacy

# One command, same on a clean clone, locally and in CI.
ci: lint test privacy validate-map

serve-fixtures:
	$(PY) fixtures/serve.py

validate-map:
	$(PY) tools/issue_map.py validate

next:
	$(PY) tools/issue_map.py next

hooks:
	git config core.hooksPath tools/hooks
	@echo "commit-msg hook installed: commits get the project owner as co-author"
