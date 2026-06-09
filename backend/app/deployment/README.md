# Deployment Notes

Frontend is designed for Vercel. Backend is a FastAPI service suitable for Render, Railway, Fly.io, Azure, or Docker with persistent volumes for `data/`, `outputs/`, and any vector index.

Azure options:

- `azure_container_apps.md` for Azure Container Apps when the `Microsoft.App` provider is available.
- `azure_app_service.md` for Azure App Service on Linux when Container Apps cannot be used.

No-Azure option:

- `vercel_render_supabase_hpc.md` for Vercel Hobby, Render Free, Supabase Free, and QMUL HPC MatterGen.

MatterGen should run as a separate GPU-capable worker. Set `MATTERGEN_WORKER_URL` and `MATTERGEN_API_KEY` when a remote worker is available. Do not deploy MatterGen generation on ordinary serverless CPU hosting.
