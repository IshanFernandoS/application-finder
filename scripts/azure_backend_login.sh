#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

echo "Starting Azure device-code login. Use your university Microsoft account in the browser."
az login --use-device-code
az account list --output table
