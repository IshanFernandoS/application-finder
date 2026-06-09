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

require_env_secret_any() {
  local label="$1"
  shift
  local key
  local value
  for key in "$@"; do
    value="$(read_env_value "$key")"
    if [ -n "$value" ]; then
      printf '%s' "$value"
      return 0
    fi
  done
  echo "Missing required secret in .env or environment: $label" >&2
  exit 2
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

"$AZ" account show >/dev/null
SUBSCRIPTION_ID="$("$AZ" account show --query id -o tsv)"
SUFFIX="$(printf '%s' "$SUBSCRIPTION_ID" | tr -cd '[:alnum:]' | tr '[:upper:]' '[:lower:]' | cut -c1-8)"

APP_NAME="$(env_value_or_default AZURE_APP_NAME gap2material-em-api)"
RG="$(env_value_or_default AZURE_RESOURCE_GROUP rg-gap2material-em)"
LOCATION="$(env_value_or_default AZURE_LOCATION uksouth)"
PLAN_NAME="$(env_value_or_default AZURE_APP_SERVICE_PLAN asp-gap2material-em)"
SKU="$(env_value_or_default AZURE_APP_SERVICE_SKU B1)"
ACR_NAME="$(env_value_or_default AZURE_ACR_NAME "gap2mat${SUFFIX}")"
IMAGE_REPOSITORY="$(env_value_or_default AZURE_IMAGE_REPOSITORY gap2material-em-api)"
IMAGE_TAG="$(env_value_or_default AZURE_IMAGE_TAG latest)"

OPENAI_VALUE="$(require_env_secret_any "OPENAI_API_KEY or OPENAI_KEY" OPENAI_API_KEY OPENAI_KEY)"
ADMIN_VALUE="$(require_env_secret_any "ADMIN_API_KEY" ADMIN_API_KEY)"
SALT_VALUE="$(require_env_secret_any "ACCESS_LOG_HASH_SALT" ACCESS_LOG_HASH_SALT)"

if "$AZ" group show --name "$RG" >/dev/null 2>&1; then
  echo "Using existing resource group: $RG"
else
  echo "Creating resource group: $RG"
  "$AZ" group create --name "$RG" --location "$LOCATION" >/dev/null
fi

if "$AZ" acr show --name "$ACR_NAME" --resource-group "$RG" >/dev/null 2>&1; then
  echo "Using existing Azure Container Registry: $ACR_NAME"
else
  echo "Creating Azure Container Registry: $ACR_NAME"
  "$AZ" acr create \
    --resource-group "$RG" \
    --name "$ACR_NAME" \
    --sku Basic \
    --admin-enabled true >/dev/null
fi

echo "Building backend image in Azure Container Registry..."
"$AZ" acr build \
  --registry "$ACR_NAME" \
  --image "$IMAGE_REPOSITORY:$IMAGE_TAG" \
  --file backend/app/deployment/Dockerfile.backend \
  . >/dev/null

if "$AZ" appservice plan show --name "$PLAN_NAME" --resource-group "$RG" >/dev/null 2>&1; then
  echo "Using existing App Service plan: $PLAN_NAME"
else
  echo "Creating Linux App Service plan: $PLAN_NAME"
  "$AZ" appservice plan create \
    --name "$PLAN_NAME" \
    --resource-group "$RG" \
    --location "$LOCATION" \
    --is-linux \
    --sku "$SKU" >/dev/null
fi

REGISTRY_SERVER="$("$AZ" acr show --name "$ACR_NAME" --resource-group "$RG" --query loginServer -o tsv)"
REGISTRY_USER="$("$AZ" acr credential show --name "$ACR_NAME" --query username -o tsv)"
REGISTRY_PASS="$("$AZ" acr credential show --name "$ACR_NAME" --query 'passwords[0].value' -o tsv)"
IMAGE_NAME="${REGISTRY_SERVER}/${IMAGE_REPOSITORY}:${IMAGE_TAG}"

if "$AZ" webapp show --name "$APP_NAME" --resource-group "$RG" >/dev/null 2>&1; then
  echo "Updating existing App Service web app: $APP_NAME"
  "$AZ" webapp config container set \
    --name "$APP_NAME" \
    --resource-group "$RG" \
    --container-image-name "$IMAGE_NAME" \
    --container-registry-url "https://${REGISTRY_SERVER}" \
    --container-registry-user "$REGISTRY_USER" \
    --container-registry-password "$REGISTRY_PASS" \
    --enable-app-service-storage true >/dev/null
else
  echo "Creating App Service web app: $APP_NAME"
  "$AZ" webapp create \
    --name "$APP_NAME" \
    --resource-group "$RG" \
    --plan "$PLAN_NAME" \
    --container-image-name "$IMAGE_NAME" \
    --container-registry-url "https://${REGISTRY_SERVER}" \
    --container-registry-user "$REGISTRY_USER" \
    --container-registry-password "$REGISTRY_PASS" \
    --https-only true >/dev/null
fi

"$AZ" webapp config appsettings set \
  --name "$APP_NAME" \
  --resource-group "$RG" \
  --settings \
    OPENAI_API_KEY="$OPENAI_VALUE" \
    ADMIN_API_KEY="$ADMIN_VALUE" \
    ACCESS_LOG_HASH_SALT="$SALT_VALUE" \
    OPENAI_MODEL="${OPENAI_MODEL:-gpt-4.1}" \
    OPENAI_EMBEDDING_MODEL="${OPENAI_EMBEDDING_MODEL:-text-embedding-3-large}" \
    DATA_DIR=/home/data \
    OUTPUT_DIR=/home/outputs \
    DATABASE_URL=sqlite:////home/data/gap2material_em.db \
    VECTOR_BACKEND=chroma \
    ENABLE_ONLINE_METADATA=true \
    ENABLE_OPENAI_REASONING=true \
    ENABLE_MATTERGEN=true \
    MATTERGEN_MODE=remote \
    MATTERGEN_WORKER_URL="${MATTERGEN_WORKER_URL:-}" \
    MATTERGEN_API_KEY="${MATTERGEN_API_KEY:-}" \
    DEPLOYMENT_ENV=azure-app-service \
    FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}" \
    BACKEND_URL="https://${APP_NAME}.azurewebsites.net" \
    ENABLE_ANALYTICS=true \
    ACCESS_LOGGING_ENABLED=true \
    ACCESS_LOG_STORE_RAW_IP=false \
    ACCESS_LOG_STORE_USER_AGENT_RAW=false \
    ACCESS_LOG_GEOIP=false \
    WEBSITES_ENABLE_APP_SERVICE_STORAGE=true \
    WEBSITES_PORT=8000 \
    WEBSITES_CONTAINER_START_TIME_LIMIT=1800 >/dev/null

"$AZ" webapp restart --name "$APP_NAME" --resource-group "$RG" >/dev/null

echo "Azure App Service backend deployed:"
echo "  https://${APP_NAME}.azurewebsites.net"
echo "Health:"
echo "  https://${APP_NAME}.azurewebsites.net/api/health"
