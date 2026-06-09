# Azure App Service Backend Deployment

This is the fallback backend deployment path when Azure Container Apps is not available on the subscription.

The script uses:

- Azure Container Registry for a backend container image.
- Azure App Service for Linux with a custom container.
- App Service persistent `/home` storage for `DATA_DIR`, `OUTPUT_DIR`, and the SQLite database.
- App settings for `OPENAI_API_KEY`, `ADMIN_API_KEY`, and `ACCESS_LOG_HASH_SALT`.

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

If you cannot create a resource group, ask QMUL/Azure support for Contributor access on an existing resource group and pass it to the deploy script:

```bash
AZURE_RESOURCE_GROUP=<existing-resource-group> scripts/azure_appservice_deploy.sh
```

## Deploy

```bash
AZURE_LOCATION=uksouth scripts/azure_appservice_deploy.sh
```

Optional environment variables:

- `AZURE_RESOURCE_GROUP`, default `rg-gap2material-em`
- `AZURE_APP_NAME`, default `gap2material-em-api`
- `AZURE_LOCATION`, default `uksouth`
- `AZURE_APP_SERVICE_PLAN`, default `asp-gap2material-em`
- `AZURE_APP_SERVICE_SKU`, default `B1`
- `AZURE_ACR_NAME`
- `AZURE_IMAGE_REPOSITORY`, default `gap2material-em-api`
- `AZURE_IMAGE_TAG`, default `latest`

## MatterGen/HPC Boundary

Azure runs only the CPU backend. MatterGen GPU generation remains on QMUL Apocrita via the HPC helper scripts:

```bash
scripts/hpc_mattergen_prepare.sh
scripts/hpc_mattergen_submit.sh PATHWAY_ID outputs/pathway_constraints.json
scripts/hpc_mattergen_fetch.sh PATHWAY_ID
```

If you later expose a proper HPC-side MatterGen worker API, set `MATTERGEN_WORKER_URL` and redeploy/update the App Service.
