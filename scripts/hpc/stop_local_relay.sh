#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PID_FILE="$ROOT_DIR/outputs/hpc_jobs/local_hpc_relay.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "Application Finder local HPC relay was not running."
  exit 0
fi

relay_pid="$(cat "$PID_FILE")"
if kill -0 "$relay_pid" 2>/dev/null; then
  kill "$relay_pid"
fi
rm -f "$PID_FILE"
echo "Application Finder local HPC relay stopped."
