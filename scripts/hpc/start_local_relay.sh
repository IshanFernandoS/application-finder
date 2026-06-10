#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

RUN_DIR="$ROOT_DIR/outputs/hpc_jobs"
PID_FILE="$RUN_DIR/local_hpc_relay.pid"
LOG_FILE="$RUN_DIR/local_hpc_relay.log"
mkdir -p "$RUN_DIR"

if [ -f "$PID_FILE" ]; then
  existing_pid="$(cat "$PID_FILE")"
  if kill -0 "$existing_pid" 2>/dev/null; then
    echo "Application Finder local HPC relay is already running."
    exit 0
  fi
  rm -f "$PID_FILE"
fi

nohup "$PYTHON_BIN" "$ROOT_DIR/scripts/hpc/local_hpc_relay.py" >>"$LOG_FILE" 2>&1 &
relay_pid="$!"
echo "$relay_pid" >"$PID_FILE"
sleep 1
if ! kill -0 "$relay_pid" 2>/dev/null; then
  rm -f "$PID_FILE"
  echo "Application Finder local HPC relay failed to start. Recent log:" >&2
  tail -n 20 "$LOG_FILE" >&2 || true
  exit 1
fi
echo "Application Finder local HPC relay started."
echo "Use scripts/hpc/stop_local_relay.sh to stop it."
