# Application Finder: Vercel + Render + Supabase + QMUL HPC

This is the recommended no-Azure deployment architecture for Application Finder at the current access level:

- Frontend: Vercel Hobby.
- Backend: Render Free web service.
- Database: Supabase Free Postgres.
- Storage: Supabase Storage bucket.
- MatterGen: QMUL Apocrita HPC through SSH/Slurm helper scripts or a later HPC-side worker API.
- Analytics: internal anonymous access logger plus Vercel Web Analytics.

Render Free has an ephemeral filesystem, so the backend must not rely on local SQLite or local uploaded/report files for durable state. In this setup, Supabase Postgres stores application data and analytics logs, while Supabase Storage stores uploaded PDFs/text files, evidence backups, reports, and evaluation artifacts.

## Supabase

Create one Supabase project and add one private Storage bucket:

```text
gap2material-artifacts
```

Copy these values for Render:

- `DATABASE_URL`: Supabase Postgres connection string.
- `SUPABASE_URL`: Supabase project URL.
- `SUPABASE_SERVICE_ROLE_KEY`: server-only service role key.
- `SUPABASE_STORAGE_BUCKET`: `gap2material-artifacts`.

Do not expose `SUPABASE_SERVICE_ROLE_KEY` to Vercel or the browser.

## Render Backend

Use `backend/app/deployment/render.yaml` as the Render blueprint. Required Render environment variables:

```text
DATABASE_URL=<supabase-postgres-url>
SUPABASE_URL=<supabase-project-url>
SUPABASE_SERVICE_ROLE_KEY=<supabase-service-role-key>
OPENAI_API_KEY=<openai-api-key>
ADMIN_API_KEY=<random-admin-analytics-key>
ACCESS_LOG_HASH_SALT=<random-long-salt>
FRONTEND_URL=https://<your-vercel-app>.vercel.app
BACKEND_URL=https://<your-render-service>.onrender.com
```

Optional Render environment variables:

```text
SUPABASE_STORAGE_BUCKET=gap2material-artifacts
MATTERGEN_WORKER_URL=<future-hpc-worker-url>
MATTERGEN_API_KEY=<future-hpc-worker-key>
HPC_ENABLED=true
HPC_USERNAME=<hpc-username>
HPC_WORKDIR=<remote-workdir>
HPC_SLURM_PARTITION=<partition>
HPC_GPU_REQUEST=gpu:1
HPC_MATTERGEN_ENV=<module/conda activation command>
```

The blueprint sets:

```text
OBJECT_STORAGE_BACKEND=supabase
MATTERGEN_MODE=hpc_slurm
HPC_MODE=slurm_ssh
ENABLE_ANALYTICS=true
ACCESS_LOG_STORE_RAW_IP=false
ACCESS_LOG_STORE_USER_AGENT_RAW=false
```

## Vercel Frontend

Set this Vercel environment variable:

```text
NEXT_PUBLIC_BACKEND_URL=https://<your-render-service>.onrender.com
```

`frontend/vercel.json` enables Vercel Web Analytics with `NEXT_PUBLIC_VERCEL_ANALYTICS=true`.

## MatterGen on QMUL HPC

Render should not store or replay QMUL passwords, passcodes, or MFA flows. Use the existing interactive SSH/Slurm helpers from your local machine or from a dedicated HPC-side worker:

```bash
scripts/hpc_mattergen_prepare.sh
scripts/hpc_mattergen_submit.sh PATHWAY_ID outputs/pathway_constraints.json
scripts/hpc_mattergen_fetch.sh PATHWAY_ID
```

When a proper HPC-side worker API exists, set `MATTERGEN_WORKER_URL` and `MATTERGEN_API_KEY` in Render.

Application Finder also exposes an admin-only `/hpc` page backed by `/api/hpc/*` endpoints. Keep `HPC_ENABLED=false` until SSH key/agent, known-host, workdir, and Slurm settings are approved and tested for the deployment environment.

## Local Development

Local development still works without Supabase Storage:

```text
OBJECT_STORAGE_BACKEND=local
DATABASE_URL=sqlite:///data/gap2material_em.db
```
