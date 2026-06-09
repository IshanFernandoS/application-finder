# Azure Backend Deployment

This project can host the FastAPI backend on Azure Container Apps while MatterGen GPU generation runs separately on QMUL Apocrita HPC through Slurm.

The deployment uses:

- Azure Container Registry for the backend container image.
- Azure Container Apps for the FastAPI service.
- Azure Files mounts for persistent `/data` and `/outputs`.
- Azure Log Analytics for Container Apps logs.
- Secrets for `OPENAI_API_KEY`, `ADMIN_API_KEY`, and `ACCESS_LOG_HASH_SALT`.

No university password, MFA passcode, HPC password, or Azure token is stored in the repository.

## Login

```bash
scripts/azure_backend_login.sh
```

Use your university Microsoft account in the browser/device-code flow.

## Check Permissions

```bash
scripts/azure_check_permissions.sh
```

Container Apps requires the `Microsoft.App` provider to be registered on the subscription. If you cannot register providers or create a resource group, ask QMUL/Azure support for Contributor access on an existing resource group and for `Microsoft.App` to be registered, or use the App Service fallback in `backend/app/deployment/azure_app_service.md`.

## Deploy

```bash
AZURE_LOCATION=uksouth scripts/azure_backend_deploy.sh
```

Optional environment variables:

- `AZURE_RESOURCE_GROUP`, default `rg-gap2material-em`
- `AZURE_APP_NAME`, default `gap2material-em-api`
- `AZURE_LOCATION`, default `uksouth`
- `AZURE_CONTAINER_ENV`, default `cae-gap2material-em`
- `AZURE_ACR_NAME`
- `AZURE_STORAGE_NAME`
- `AZURE_BACKEND_CPU`, default `1.0`
- `AZURE_BACKEND_MEMORY`, default `2Gi`
- `AZURE_MIN_REPLICAS`, default `0`
- `AZURE_MAX_REPLICAS`, default `2`

## Status

```bash
scripts/azure_backend_status.sh
```

## MatterGen/HPC Boundary

Azure should not store or replay your QMUL login credentials. MatterGen should run via the interactive Apocrita Slurm helper scripts:

```bash
scripts/hpc_mattergen_prepare.sh
scripts/hpc_mattergen_submit.sh PATHWAY_ID outputs/pathway_constraints.json
scripts/hpc_mattergen_fetch.sh PATHWAY_ID
```

If you later expose a proper HPC-side MatterGen worker API, set `MATTERGEN_WORKER_URL` and redeploy/update the Azure Container App.
