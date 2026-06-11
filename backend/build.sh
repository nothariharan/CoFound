#!/usr/bin/env bash
set -euo pipefail

pip install -r requirements.txt

# MCP uses npx at runtime — no global npm install needed on hosted environments.
