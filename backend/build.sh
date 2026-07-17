#!/usr/bin/env bash
set -euo pipefail

python --version
py_minor="$(python -c 'import sys; print(sys.version_info.minor)')"
py_major="$(python -c 'import sys; print(sys.version_info.major)')"
if [ "$py_major" -ne 3 ] || [ "$py_minor" -lt 11 ] || [ "$py_minor" -gt 12 ]; then
  echo "ERROR: Python 3.11 or 3.12 required (found ${py_major}.${py_minor})."
  echo "Set environment variable PYTHON_VERSION=3.11.9 on your host and redeploy."
  exit 1
fi

pip install --no-cache-dir -r requirements.txt
