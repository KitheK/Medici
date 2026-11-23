#!/usr/bin/env bash
# Start-of-session health check. Passes on a clean clone; run it before any issue work.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PY:-python3}"

echo "== context files =="
for f in AGENTS.md CLAUDE.md progress.md issue_map.json Makefile; do
  [ -f "$f" ] || { echo "missing $f"; exit 1; }
done
head -n 1 CLAUDE.md | grep -qx '@AGENTS.md' || { echo "CLAUDE.md must start with @AGENTS.md"; exit 1; }

echo "== commit hook =="
[ "$(git config core.hooksPath 2>/dev/null)" = "tools/hooks" ] || echo "warning: run: make hooks (so commits get the co-author trailer)"

echo "== issue map =="
$PY tools/issue_map.py validate

echo "== lint and tests =="
$PY -m ruff check .
$PY -m pytest -q

echo "== next ready issues =="
$PY tools/issue_map.py next --all || true

echo "init ok"
