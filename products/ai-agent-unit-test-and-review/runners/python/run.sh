#!/usr/bin/env bash
set -euo pipefail
# Install project deps if present
if [[ -f "requirements.txt" ]]; then pip install --no-cache-dir -r requirements.txt || true; fi
# Create coverage dir
mkdir -p .coverage
# Run tests with coverage if tests exist
if compgen -G "tests/*.py" > /dev/null; then
  # MODIFIED: Output coverage to a term report AND to a machine-readable XML file
  pytest -q --maxfail=1 --disable-warnings --cov=. --cov-report=term-missing --cov-report=xml || true
else
  echo "[python] No tests found"; exit 0
fi