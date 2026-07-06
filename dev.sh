#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Kill both child processes when Ctrl+C is pressed or script exits
trap 'kill 0' SIGINT SIGTERM EXIT

echo "▶ backend  http://localhost:8000"
echo "▶ frontend http://localhost:3000"
echo "(Ctrl+C to stop both)"
echo ""

"$ROOT/.venv/bin/uvicorn" backend.main:app \
  --reload --port 8000 \
  2>&1 | sed $'s/^/\033[34m[backend] \033[0m/' &

cd "$ROOT/frontend" && npm run dev \
  2>&1 | sed $'s/^/\033[32m[frontend]\033[0m /' &

wait
