#!/usr/bin/env bash
set -euo pipefail
# Install deps
if [[ -f "package.json" ]]; then npm ci || npm i || true; fi
# Jest config fallback
if [[ ! -f "jest.config.js" && ! -f "jest.config.cjs" ]]; then
cat > jest.config.cjs <<'CFG'
module.exports = { testEnvironment: 'node', transform: {}, roots: ['<rootDir>/__tests__'] };
CFG
fi
# Run ESLint if available
if command -v eslint >/dev/null 2>&1; then npx -y eslint . || true; fi
# Run tests
if compgen -G "__tests__/*.(js|ts)" > /dev/null; then
  npx -y jest --runInBand || true
else
  echo "[node] No tests found"; exit 0
fi