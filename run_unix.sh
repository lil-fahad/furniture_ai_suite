#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

host="${HOST:-127.0.0.1}"
port="${PORT:-8000}"
reload="${RELOAD:-false}"
uvicorn_args=(secure_app:app --host "$host" --port "$port")
if [[ "$reload" == "true" ]]; then
  uvicorn_args+=(--reload)
fi

exec python -m uvicorn "${uvicorn_args[@]}"
