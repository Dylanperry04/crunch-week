#!/usr/bin/env sh
set -eu
# App Service activates its Python environment before this startup script runs.
exec python -m uvicorn crunch_week.api:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
