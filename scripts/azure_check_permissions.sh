#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PATH="$HOME/.local/bin:$PATH"
AZ="${AZURE_CLI:-}"
if [ -z "$AZ" ]; then
  if command -v az >/dev/null 2>&1; then
    AZ="az"
  elif [ -x "$HOME/.local/bin/az" ]; then
    AZ="$HOME/.local/bin/az"
  else
    echo "Azure CLI not found. Run scripts/azure_backend_login.sh after installing Azure CLI." >&2
    exit 127
  fi
fi

RG="${AZURE_RESOURCE_GROUP:-rg-gap2material-em}"
LOCATION="${AZURE_LOCATION:-uksouth}"

read_env_value() {
  local key="$1"
  local current="${!key:-}"
  if [ -n "$current" ]; then
    printf '%s' "$current"
    return 0
  fi

  if [ ! -f .env ]; then
    return 0
  fi

  local line
  line="$(grep -E "^${key}=" .env | tail -n 1 || true)"
  if [ -z "$line" ]; then
    return 0
  fi
  printf '%s' "${line#*=}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
}

env_value_or_default() {
  local key="$1"
  local default="$2"
  local value
  value="$(read_env_value "$key")"
  if [ -n "$value" ]; then
    printf '%s' "$value"
  else
    printf '%s' "$default"
  fi
}

RG="$(env_value_or_default AZURE_RESOURCE_GROUP "$RG")"
LOCATION="$(env_value_or_default AZURE_LOCATION "$LOCATION")"

"$AZ" account show --query '{user:user.name, subscription:name, subscriptionId:id, tenant:tenantDisplayName}' -o table

echo
echo "Provider registration state:"
"$AZ" provider list \
  --query "[?namespace=='Microsoft.App' || namespace=='Microsoft.ContainerRegistry' || namespace=='Microsoft.Storage' || namespace=='Microsoft.Web'].{namespace:namespace,state:registrationState}" \
  -o table

echo
echo "Visible resource groups:"
"$AZ" group list --query "[].{name:name,location:location}" -o table

echo
echo "Checking target resource group: $RG"
if "$AZ" group show --name "$RG" >/dev/null 2>&1; then
  echo "Readable: yes"
else
  echo "Readable: no"
fi

echo
echo "Testing whether this account can create the target resource group if needed..."
if "$AZ" group show --name "$RG" >/dev/null 2>&1; then
  echo "Create test skipped because the resource group already exists."
elif "$AZ" group create --name "$RG" --location "$LOCATION" --tags purpose=gap2material-permission-check >/dev/null 2>&1; then
  echo "Create test passed: resource group created."
else
  echo "Create test failed: request Contributor/Owner on a resource group, or permission to create one."
fi
