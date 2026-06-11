#!/usr/bin/env bash
set -euo pipefail

pip install -r requirements.txt

if command -v npm >/dev/null 2>&1; then
  npm install -g mongodb-mcp-server@0.3.0 || true
fi
