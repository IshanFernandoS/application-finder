#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

RG="${AZURE_RESOURCE_GROUP:-rg-gap2material-em}"
APP_NAME="${AZURE_APP_NAME:-gap2material-em-api}"

FQDN="$(az containerapp show --name "$APP_NAME" --resource-group "$RG" --query properties.configuration.ingress.fqdn -o tsv)"
echo "Backend URL: https://${FQDN}"
curl -fsS "https://${FQDN}/api/health"
