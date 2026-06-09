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

APP_NAME="${AZURE_APP_NAME:-gap2material-em-api}"
RG="${AZURE_RESOURCE_GROUP:-rg-gap2material-em}"
LOCATION="${AZURE_LOCATION:-uksouth}"
ENV_NAME="${AZURE_CONTAINER_ENV:-cae-gap2material-em}"
ACR_NAME="${AZURE_ACR_NAME:-gap2materialem$((10000 + RANDOM % 89999))}"
STORAGE_NAME="${AZURE_STORAGE_NAME:-gap2materialem$((10000 + RANDOM % 89999))}"
IMAGE_TAG="${AZURE_IMAGE_TAG:-latest}"
DATA_SHARE="${AZURE_DATA_SHARE:-gap2material-data}"
OUTPUT_SHARE="${AZURE_OUTPUT_SHARE:-gap2material-outputs}"
LOG_WORKSPACE="${AZURE_LOG_WORKSPACE:-law-gap2material-em}"
CPU="${AZURE_BACKEND_CPU:-1.0}"
MEMORY="${AZURE_BACKEND_MEMORY:-2Gi}"
MIN_REPLICAS="${AZURE_MIN_REPLICAS:-0}"
MAX_REPLICAS="${AZURE_MAX_REPLICAS:-2}"

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

APP_NAME="$(env_value_or_default AZURE_APP_NAME "$APP_NAME")"
RG="$(env_value_or_default AZURE_RESOURCE_GROUP "$RG")"
LOCATION="$(env_value_or_default AZURE_LOCATION "$LOCATION")"
ENV_NAME="$(env_value_or_default AZURE_CONTAINER_ENV "$ENV_NAME")"
ACR_NAME="$(env_value_or_default AZURE_ACR_NAME "$ACR_NAME")"
STORAGE_NAME="$(env_value_or_default AZURE_STORAGE_NAME "$STORAGE_NAME")"
IMAGE_TAG="$(env_value_or_default AZURE_IMAGE_TAG "$IMAGE_TAG")"
DATA_SHARE="$(env_value_or_default AZURE_DATA_SHARE "$DATA_SHARE")"
OUTPUT_SHARE="$(env_value_or_default AZURE_OUTPUT_SHARE "$OUTPUT_SHARE")"
LOG_WORKSPACE="$(env_value_or_default AZURE_LOG_WORKSPACE "$LOG_WORKSPACE")"
CPU="$(env_value_or_default AZURE_BACKEND_CPU "$CPU")"
MEMORY="$(env_value_or_default AZURE_BACKEND_MEMORY "$MEMORY")"
MIN_REPLICAS="$(env_value_or_default AZURE_MIN_REPLICAS "$MIN_REPLICAS")"
MAX_REPLICAS="$(env_value_or_default AZURE_MAX_REPLICAS "$MAX_REPLICAS")"

OPENAI_VALUE="$(require_env_secret_any "OPENAI_API_KEY or OPENAI_KEY" OPENAI_API_KEY OPENAI_KEY)"
ADMIN_VALUE="$(require_env_secret_any "ADMIN_API_KEY" ADMIN_API_KEY)"
SALT_VALUE="$(require_env_secret_any "ACCESS_LOG_HASH_SALT" ACCESS_LOG_HASH_SALT)"

"$AZ" account show >/dev/null

"$AZ" extension add --name containerapp --upgrade >/dev/null

if "$AZ" group show --name "$RG" >/dev/null 2>&1; then
  echo "Using existing resource group: $RG"
else
  "$AZ" group create --name "$RG" --location "$LOCATION" >/dev/null
fi

"$AZ" acr create \
  --resource-group "$RG" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true >/dev/null

"$AZ" acr build \
  --registry "$ACR_NAME" \
  --image "$APP_NAME:$IMAGE_TAG" \
  --file backend/app/deployment/Dockerfile.backend \
  . >/dev/null

"$AZ" monitor log-analytics workspace create \
  --resource-group "$RG" \
  --workspace-name "$LOG_WORKSPACE" \
  --location "$LOCATION" >/dev/null

CUSTOMER_ID="$("$AZ" monitor log-analytics workspace show --resource-group "$RG" --workspace-name "$LOG_WORKSPACE" --query customerId -o tsv)"
SHARED_KEY="$("$AZ" monitor log-analytics workspace get-shared-keys --resource-group "$RG" --workspace-name "$LOG_WORKSPACE" --query primarySharedKey -o tsv)"

"$AZ" containerapp env create \
  --name "$ENV_NAME" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --logs-workspace-id "$CUSTOMER_ID" \
  --logs-workspace-key "$SHARED_KEY" >/dev/null

"$AZ" storage account create \
  --resource-group "$RG" \
  --name "$STORAGE_NAME" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2 >/dev/null

STORAGE_KEY="$("$AZ" storage account keys list --resource-group "$RG" --account-name "$STORAGE_NAME" --query '[0].value' -o tsv)"

"$AZ" storage share-rm create \
  --resource-group "$RG" \
  --storage-account "$STORAGE_NAME" \
  --name "$DATA_SHARE" \
  --quota 100 >/dev/null

"$AZ" storage share-rm create \
  --resource-group "$RG" \
  --storage-account "$STORAGE_NAME" \
  --name "$OUTPUT_SHARE" \
  --quota 100 >/dev/null

"$AZ" containerapp env storage set \
  --resource-group "$RG" \
  --name "$ENV_NAME" \
  --storage-name data-volume \
  --azure-file-account-name "$STORAGE_NAME" \
  --azure-file-account-key "$STORAGE_KEY" \
  --azure-file-share-name "$DATA_SHARE" \
  --access-mode ReadWrite >/dev/null

"$AZ" containerapp env storage set \
  --resource-group "$RG" \
  --name "$ENV_NAME" \
  --storage-name outputs-volume \
  --azure-file-account-name "$STORAGE_NAME" \
  --azure-file-account-key "$STORAGE_KEY" \
  --azure-file-share-name "$OUTPUT_SHARE" \
  --access-mode ReadWrite >/dev/null

REGISTRY_SERVER="$("$AZ" acr show --name "$ACR_NAME" --resource-group "$RG" --query loginServer -o tsv)"
REGISTRY_USER="$("$AZ" acr credential show --name "$ACR_NAME" --query username -o tsv)"
REGISTRY_PASS="$("$AZ" acr credential show --name "$ACR_NAME" --query 'passwords[0].value' -o tsv)"

TMP_YAML="$(mktemp)"
cat > "$TMP_YAML" <<YAML
properties:
  configuration:
    activeRevisionsMode: Single
    ingress:
      external: true
      targetPort: 8000
      transport: auto
    registries:
      - server: ${REGISTRY_SERVER}
        username: ${REGISTRY_USER}
        passwordSecretRef: registry-password
    secrets:
      - name: registry-password
        value: "${REGISTRY_PASS}"
      - name: openai-key
        value: "${OPENAI_VALUE}"
      - name: admin-api-key
        value: "${ADMIN_VALUE}"
      - name: access-log-hash-salt
        value: "${SALT_VALUE}"
  template:
    scale:
      minReplicas: ${MIN_REPLICAS}
      maxReplicas: ${MAX_REPLICAS}
    containers:
      - name: ${APP_NAME}
        image: ${REGISTRY_SERVER}/${APP_NAME}:${IMAGE_TAG}
        resources:
          cpu: ${CPU}
          memory: ${MEMORY}
        env:
          - name: OPENAI_API_KEY
            secretRef: openai-key
          - name: ADMIN_API_KEY
            secretRef: admin-api-key
          - name: ACCESS_LOG_HASH_SALT
            secretRef: access-log-hash-salt
          - name: OPENAI_MODEL
            value: "${OPENAI_MODEL:-gpt-4.1}"
          - name: OPENAI_EMBEDDING_MODEL
            value: "${OPENAI_EMBEDDING_MODEL:-text-embedding-3-large}"
          - name: DATA_DIR
            value: /data
          - name: OUTPUT_DIR
            value: /outputs
          - name: DATABASE_URL
            value: sqlite:////data/gap2material_em.db
          - name: VECTOR_BACKEND
            value: chroma
          - name: ENABLE_ONLINE_METADATA
            value: "true"
          - name: ENABLE_OPENAI_REASONING
            value: "true"
          - name: ENABLE_MATTERGEN
            value: "true"
          - name: MATTERGEN_MODE
            value: remote
          - name: MATTERGEN_WORKER_URL
            value: "${MATTERGEN_WORKER_URL:-}"
          - name: DEPLOYMENT_ENV
            value: azure
          - name: FRONTEND_URL
            value: "${FRONTEND_URL:-http://localhost:3000}"
          - name: BACKEND_URL
            value: https://placeholder
          - name: ENABLE_ANALYTICS
            value: "true"
          - name: ACCESS_LOGGING_ENABLED
            value: "true"
          - name: ACCESS_LOG_STORE_RAW_IP
            value: "false"
          - name: ACCESS_LOG_STORE_USER_AGENT_RAW
            value: "false"
          - name: ACCESS_LOG_GEOIP
            value: "false"
        volumeMounts:
          - volumeName: data-volume
            mountPath: /data
          - volumeName: outputs-volume
            mountPath: /outputs
    volumes:
      - name: data-volume
        storageType: AzureFile
        storageName: data-volume
      - name: outputs-volume
        storageType: AzureFile
        storageName: outputs-volume
YAML

"$AZ" containerapp create \
  --name "$APP_NAME" \
  --resource-group "$RG" \
  --environment "$ENV_NAME" \
  --yaml "$TMP_YAML" >/dev/null

rm -f "$TMP_YAML"

"$AZ" containerapp update \
  --name "$APP_NAME" \
  --resource-group "$RG" \
  --set-env-vars BACKEND_URL="https://$("$AZ" containerapp show --name "$APP_NAME" --resource-group "$RG" --query properties.configuration.ingress.fqdn -o tsv)" >/dev/null

FQDN="$("$AZ" containerapp show --name "$APP_NAME" --resource-group "$RG" --query properties.configuration.ingress.fqdn -o tsv)"
echo "Azure backend deployed:"
echo "  https://${FQDN}"
echo "Health:"
echo "  https://${FQDN}/api/health"
