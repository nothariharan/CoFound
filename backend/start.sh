#!/usr/bin/env bash
set -euo pipefail

# Free Render instances are ~512 MB — stay single-worker and bound concurrency.
WORKERS="${WEB_CONCURRENCY:-1}"
LIMIT="${UVICORN_LIMIT_CONCURRENCY:-20}"

export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

exec uvicorn main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${WORKERS}" \
  --limit-concurrency "${LIMIT}" \
  --timeout-keep-alive 5
