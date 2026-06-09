#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p outputs/logs "$HOME/.local/bin"
NODE_DIR="$HOME/.local/share/gap2material-em/node-v24.16.0-darwin-arm64/bin"
DEV_PATH="$HOME/.local/bin:$PATH"
if [ -d "$NODE_DIR" ]; then
  DEV_PATH="$NODE_DIR:$DEV_PATH"
fi

start_detached() {
  local pidfile="$1"
  local logfile="$2"
  local cwd="$3"
  shift 3
  PATH="$DEV_PATH" .venv/bin/python - "$pidfile" "$logfile" "$cwd" "$@" <<'PY'
from __future__ import annotations

import os
import subprocess
import sys

pidfile, logfile, cwd, *cmd = sys.argv[1:]
env = os.environ.copy()
with open(logfile, "ab") as handle:
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
with open(pidfile, "w", encoding="utf-8") as handle:
    handle.write(str(process.pid))
PY
}

if [ -f outputs/backend.pid ] && kill -0 "$(cat outputs/backend.pid)" 2>/dev/null; then
  echo "Backend already running on PID $(cat outputs/backend.pid)"
else
  start_detached outputs/backend.pid outputs/logs/backend.log "$ROOT_DIR" \
    "$ROOT_DIR/.venv/bin/python" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
  echo "Backend started on http://127.0.0.1:8000"
fi

if [ -f outputs/frontend.pid ] && kill -0 "$(cat outputs/frontend.pid)" 2>/dev/null; then
  echo "Frontend already running on PID $(cat outputs/frontend.pid)"
else
  start_detached outputs/frontend.pid outputs/logs/frontend.log "$ROOT_DIR/frontend" \
    npm run dev -- --hostname 127.0.0.1 --port 3000
  echo "Frontend started on http://127.0.0.1:3000"
fi
