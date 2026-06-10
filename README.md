# Application Finder

Application Finder — Electromagnetic Application-Space-Guided Generative Inverse Materials Design Platform.

Application Finder builds a scoped electromagnetic Application Space from real literature, detects underexplored descriptor regions, retrieves boundary evidence, reasons through FBS-PM pathways, translates material-property envelopes into MatterGen-compatible proxies, and exports validation-ready reports.

The internal architecture/package name may still appear as `gap2material-em` in deployment resources and code paths.

This is not a toy workflow. The main pipeline does not fabricate descriptors, pathways, evidence, candidate materials, or generated structures when a required capability is unavailable. Missing OpenAI, missing PDF parsers, or missing MatterGen return explicit configuration/status errors.

## Scientific Scope

The default scope is `electromagnetic_functional_materials`.

It covers electromagnetic functional materials and devices across RF, microwave, millimetre-wave, THz, infrared, optical, and photonic applications, including antennas, sensing, metasurfaces, absorbers, radomes, EMI shielding, tunable dielectrics/conductors, phase-change materials, plasmonics, coatings, adaptive skins, high-temperature EM materials, and thermal/optical-control devices.

The first material scope includes oxides, chalcogenides, nitrides, carbides, ceramics, ferrites, ferroelectrics, piezoelectrics, magneto-dielectrics, transparent conducting oxides, phase-change inorganic materials, plasmonic metals and refractory plasmonics, MXenes/inorganic 2D materials linked to EM properties, conductive ceramics, high-entropy ceramics/carbides/nitrides, and inorganic semiconductors.

Weaponized framing is avoided. Literature terms such as stealth or camouflage should be treated as electromagnetic signature management or thermal/optical control in civilian scientific contexts.

## FBS-PM Chain

The system must never jump directly from an application to a material. Every recommendation passes through:

`Application-space gap -> pseudo-application -> Function -> Behaviour / physical EM mechanism -> Structure / device realization pathway -> EM material-property envelope -> material candidate -> evidence / uncertainty / validation status`

## Architecture

- `backend/`: FastAPI, SQLAlchemy, Pydantic schemas, ingestion, retrieval, Application Space, gap detection, FBS-PM, MatterGen, validation, evaluation, analytics, reports.
- `frontend/`: Next.js App Router, TypeScript, Tailwind, Plotly Application Space map, React Flow pathway graph, research dashboards.
- `data/`: PDFs, evidence notes, Zotero exports, metadata, indexes, labels, evaluations.
- `outputs/`: reports, result JSON, evidence CSV, MatterGen job outputs.
- `tools/`: optional local MatterGen checkout or worker tooling.

## Environment

Copy `.env.example` to `.env` and set real values locally. The existing `.env` is intentionally not overwritten.

Important variables:

- `OPENAI_API_KEY`: required for descriptor extraction and FBS-PM generation.
- `OPENAI_KEY`: accepted as a local backward-compatible alias, but `OPENAI_API_KEY` is the documented name.
- `OPENAI_MODEL`: reasoning model.
- `OPENAI_EMBEDDING_MODEL`: embedding model.
- `UNPAYWALL_EMAIL`: optional public API contact email, defaulting to `h.i.s.fernando@qmul.ac.uk`.
- `ENABLE_PUBLIC_FULL_TEXT_FETCH`: tries open-access full text for public search ingestion before falling back to abstracts/metadata.
- `PUBLIC_FULL_TEXT_MAX_PAPERS_PER_REQUEST`, `PUBLIC_FULL_TEXT_MAX_CHUNKS_PER_PAPER`, `PUBLIC_FULL_TEXT_DESCRIPTOR_CHUNKS_PER_PAPER`: caps for full-text retrieval and descriptor extraction.
- `DATABASE_URL`: defaults to SQLite at `data/gap2material_em.db`.
- `MATTERGEN_PATH`, `MATTERGEN_WORKER_URL`, `MATTERGEN_API_KEY`: MatterGen local/remote worker settings.
- `HPC_ENABLED`, `HPC_MODE`, `HPC_HOST`, `HPC_USERNAME`, `HPC_SSH_KEY_PATH`, `HPC_WORKDIR`: optional admin-only SSH/Slurm compute worker settings.
- `ADMIN_API_KEY`: required for analytics/admin endpoints. On Vercel, set it as a server-side environment variable for the frontend admin proxy; do not expose it as `NEXT_PUBLIC_*`.

Descriptor extraction uses uploaded full papers first, then open-access public full text when available through arXiv, PMC, Unpaywall, or search-provider OA links, then abstracts/metadata as fallback. Do not automate university logins, publisher logins, cookie reuse, proxy logins, credential storage, paywall bypassing, or paywalled scraping. Put legally accessible PDFs into `data/pdfs/`.

## Local Backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Health:

```bash
curl http://localhost:8000/api/health
```

## Local Frontend

Node is required.

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Literature Ingestion

Put files in:

- `data/pdfs/` for PDFs.
- `data/evidence/` for `.txt`, `.md`, or `.markdown` notes.
- `data/zotero/` for Zotero CSV exports.

Run:

```bash
curl -X POST http://localhost:8000/api/ingest/files
curl -X POST http://localhost:8000/api/ingest/zotero
```

Local ingestion preserves document id, title, DOI if found, source type, file path, page, section, snippet, and evidence id. PDF parsing requires `pymupdf` or `pypdf`.

Public metadata search uses public APIs only:

```bash
curl -X POST "http://localhost:8000/api/ingest/public-search?query=THz%20phase%20change%20metasurface&limit=10"
```

## Descriptor Extraction

Descriptor extraction requires OpenAI. If the key or SDK is missing, the backend returns a configuration/dependency error.

```bash
curl -X POST "http://localhost:8000/api/ingest/extract-descriptors?scope_id=electromagnetic_functional_materials&limit=50"
```

The extractor validates outputs into `ApplicationNode` records containing application, domain, function, stimulus/response, frequency/wavelength regime, device type, architecture, EM mechanism, material class, material names, property requirements, evidence ids, year, and confidence.

## Build Application Space

After descriptor extraction:

```bash
curl -X POST "http://localhost:8000/api/application-space/build?scope_id=electromagnetic_functional_materials"
curl "http://localhost:8000/api/application-space?scope_id=electromagnetic_functional_materials"
```

The backend uses descriptor text/features, UMAP if installed with PCA fallback, and HDBSCAN if installed with KMeans fallback. Coordinates, clusters, summaries, evidence counts, reducer/clusterer metadata, and build metadata are persisted.

## Detect Gaps

```bash
curl -X POST "http://localhost:8000/api/gaps/detect?scope_id=electromagnetic_functional_materials"
curl "http://localhost:8000/api/gaps?scope_id=electromagnetic_functional_materials"
```

Gap scores include novelty/density, neighbour diversity, boundary evidence, feasibility, MatterGen compatibility, uncertainty, and overall score. Gap characterization creates pseudo-application hypotheses from boundary descriptors rather than material shortcuts.

## Boundary-RAG

```bash
curl -X POST http://localhost:8000/api/gaps/GAP_ID/retrieve-evidence
```

Boundary-RAG plans EM-specific queries from nearby clusters and descriptors, then retrieves citation-preserving chunks with BM25/hybrid retrieval boundaries.

## FBS-PM Pathways

```bash
curl -X POST http://localhost:8000/api/gaps/GAP_ID/generate-pathways
curl http://localhost:8000/api/pathways/PATHWAY_ID
curl -X POST http://localhost:8000/api/pathways/PATHWAY_ID/validate-evidence
curl -X POST http://localhost:8000/api/pathways/PATHWAY_ID/rank
```

FBS-PM generation requires OpenAI structured output and Pydantic validation. Invalid model output is rejected and not patched with fake data.

## MatterGen

MatterGen is optional and must run locally with a compatible GPU environment or as a separate remote worker.

```bash
bash scripts/setup_mattergen.sh
curl http://localhost:8000/api/mattergen/status
curl -X POST "http://localhost:8000/api/pathways/PATHWAY_ID/mattergen/translate-constraints"
curl -X POST "http://localhost:8000/api/mattergen/jobs?pathway_id=PATHWAY_ID"
```

The constraint translator maps chemistry family, element inclusion/exclusion, oxide/nitride/carbide/chalcogenide/ferrite/ceramic class, band gap, bulk modulus, magnetic density, and stability/formation-energy proxies where possible.

Unsupported EM properties are retained as validation requirements:

- loss tangent
- complex permittivity/permeability
- refractive index and extinction spectra
- emissivity spectra
- RF absorption bandwidth
- impedance matching
- device-level resonance
- cycling stability
- oxidation resistance
- processability
- flexibility
- interface adhesion

Generated candidates are always unvalidated until validation hooks pass.

### QMUL Apocrita HPC

For GPU generation on Apocrita, use the interactive SSH/Slurm helpers:

```bash
scripts/hpc_mattergen_prepare.sh
scripts/hpc_mattergen_submit.sh PATHWAY_ID outputs/pathway_constraints.json
scripts/hpc_mattergen_fetch.sh PATHWAY_ID
```

These scripts do not store passwords or passcodes. Apocrita uses Slurm for jobs, so GPU generation should be submitted as a batch job rather than run directly on the login node. See [backend/app/deployment/hpc_mattergen.md](backend/app/deployment/hpc_mattergen.md).

## Using HPC as a Compute Worker

Application Finder can use an HPC account as an optional compute worker for MatterGen jobs, validation jobs, large embedding/indexing jobs, bulk PDF processing, and future DFT/EM-simulation workflows. The public web backend is not an HPC web server; it only submits jobs through SSH and the scheduler.

Why this boundary exists:

- HPC login nodes should not host the public backend.
- Heavy computation should not run on the login node.
- Long-running work must be submitted through the institution scheduler, such as Slurm `sbatch`.
- The hosted backend should communicate with HPC only through the safe worker adapter.

Safe authentication:

- Use SSH keys or SSH agent forwarding.
- Configure the key path with `HPC_SSH_KEY_PATH` only when appropriate.
- Keep `HPC_STRICT_HOST_KEY_CHECKING=true` where possible.
- On hosted platforms, set `HPC_KNOWN_HOSTS_PATH` to a secret-file path containing the approved host key.
- Do not store HPC passwords, passcodes, one-time tokens, SSH private keys, or MFA flows in code, config, database, logs, `.env`, shell history, or notebooks.
- Do not print SSH keys or secret paths in logs.

Slurm configuration:

```text
HPC_ENABLED=false
HPC_MODE=slurm_ssh
HPC_HOST=login.hpc.qmul.ac.uk
HPC_USERNAME=
HPC_SSH_KEY_PATH=
HPC_WORKDIR=
HPC_SLURM_PARTITION=
HPC_SLURM_ACCOUNT=
HPC_GPU_REQUEST=
HPC_TIME_LIMIT=04:00:00
HPC_CPUS_PER_TASK=8
HPC_MEM=32G
HPC_PYTHON_MODULE=
HPC_MATTERGEN_ENV=
HPC_RSYNC_EXTRA_ARGS=
HPC_STRICT_HOST_KEY_CHECKING=true
HPC_KNOWN_HOSTS_PATH=
HPC_SSH_CONTROL_PATH=
HPC_QUEUE_ONLY=false
```

If your institution requires password after public-key authentication, start a local SSH control master first:

```bash
scripts/hpc/start_control_master.sh
```

Enter the HPC password interactively in your terminal. Application Finder can then reuse `HPC_SSH_CONTROL_PATH` for non-interactive `ssh`, `rsync`, and Slurm commands without storing or automating the password.

Hosted backend with local relay:

Set `HPC_QUEUE_ONLY=true` on Render when the hosted backend must not store an SSH private key. In this mode, Render creates queued HPC job records, and a local relay running on your Mac submits/polls/retrieves the jobs using your existing SSH agent, Apple Keychain, or SSH control master.

```bash
ADMIN_API_KEY=... AF_REMOTE_BACKEND_URL=https://application-finder-backend.onrender.com \
  scripts/hpc/local_hpc_relay.py
```

Convenience launchers:

```bash
scripts/hpc/start_control_master.sh
scripts/hpc/start_local_relay.sh
scripts/hpc/stop_local_relay.sh
scripts/hpc/stop_control_master.sh
```

This keeps the web-app user experience non-interactive while avoiding password automation and avoiding upload of your personal SSH private key.

Admin-only HPC API:

```bash
curl -H "x-admin-api-key: $ADMIN_API_KEY" http://localhost:8000/api/hpc/status
curl -X POST -H "x-admin-api-key: $ADMIN_API_KEY" http://localhost:8000/api/hpc/check-connection
curl -X POST -H "x-admin-api-key: $ADMIN_API_KEY" http://localhost:8000/api/hpc/check-slurm
curl -X POST -H "x-admin-api-key: $ADMIN_API_KEY" http://localhost:8000/api/hpc/check-mattergen
```

Submit MatterGen only from an FBS-PM pathway:

```bash
curl -X POST http://localhost:8000/api/hpc/jobs \
  -H "content-type: application/json" \
  -H "x-admin-api-key: $ADMIN_API_KEY" \
  -d '{"job_type":"mattergen_generation","pathway_id":"PATHWAY_ID"}'
```

The workflow is:

`Pathway -> property envelope -> MatterGen constraints -> HPC MatterGen job -> generated structure files -> candidate records -> validation hooks`

The worker:

1. Creates a job ID.
2. Writes input JSON and job metadata.
3. Transfers inputs to `HPC_WORKDIR/jobs/JOB_ID`.
4. Generates a Slurm script.
5. Submits using `sbatch`.
6. Stores the returned Slurm job ID.
7. Polls status with `squeue` and `sacct`.
8. Retrieves outputs/logs with `rsync`.
9. Parses generated structure files into Application Finder candidate records.
10. Shows status, logs, outputs, and validation state in the `/hpc` admin page.

Standalone helper scripts are also available:

```bash
scripts/hpc/submit_mattergen_job.sh PATHWAY_ID outputs/pathway_constraints.json
scripts/hpc/check_job_status.sh SLURM_JOB_ID
scripts/hpc/retrieve_job_outputs.sh HPC_JOB_ID
```

Troubleshooting:

- `Permission denied (publickey)` means SSH key or agent configuration is not accepted.
- `Host key verification failed` means `known_hosts` needs to be populated or checked.
- `sbatch: command not found` means Slurm is not available on the remote PATH or modules need loading.
- `MatterGen environment check failed` means `HPC_MATTERGEN_ENV` should load/activate the environment that contains MatterGen.
- Missing outputs usually means the Slurm job failed; retrieve logs and inspect `slurm-*.err`.

Policy note: check and follow your institution's HPC rules before enabling Application Finder's HPC worker. The automation is intended to submit legitimate scheduled jobs for your own account, not to bypass login, MFA, scheduler, or usage policies.

## Validation Hooks

Candidate validation includes hooks for pymatgen parsing, composition sanity checks, Materials Project lookup, dielectric property lookup, optical constants lookup, DFT export, EM simulation export for CST/HFSS/COMSOL, and user-uploaded validation results.

## Evaluations and Baselines

```bash
curl -X POST "http://localhost:8000/api/evals/run?scope_id=electromagnetic_functional_materials&mode=full_method"
curl http://localhost:8000/api/evals/results
curl -X POST http://localhost:8000/api/evals/baselines/run \
  -H "content-type: application/json" \
  -d '{"mode":"baseline_nearest_neighbour","scope_id":"electromagnetic_functional_materials","gap_id":"GAP_ID"}'
```

Implemented evaluation areas:

- corpus and descriptor quality
- Application Space coherence
- gap detection metrics
- retrieval relevance/citation coverage
- FBS-PM completeness and no-direct-jump checks
- MatterGen constraint retention
- material candidate validation hooks
- time-split support scaffold
- expert review CSV export

Baseline modes:

- `baseline_direct_llm`
- `baseline_standard_rag`
- `baseline_nearest_neighbour`
- `baseline_fbs_pm_no_boundary_rag`
- `full_method`

LLM baselines require OpenAI and fail explicitly if it is not configured.

## Reports

```bash
curl -X POST http://localhost:8000/api/reports/GAP_ID
curl http://localhost:8000/api/reports
```

Reports write:

- `outputs/report_GAPID_TIMESTAMP.md`
- `outputs/result_GAPID_TIMESTAMP.json`
- `outputs/evidence_GAPID_TIMESTAMP.csv`
- evaluation JSON artifacts under `outputs/`

Reports include "Generated by Application Finder", scope, corpus/evidence summary, gap summary, boundary descriptors, pseudo-applications, retrieval strategy, evidence table, FBS-PM pathways, property envelopes, candidates, MatterGen constraints, validation status, unsupported properties, limitations, and recommended validation steps.

## Anonymous Analytics

Internal analytics are privacy preserving by default:

- no names
- no raw IP storage unless explicitly enabled
- no raw user-agent storage unless explicitly enabled
- no invasive fingerprinting
- no cross-site tracking
- daily HMAC-SHA256 anonymous visitor/session hashes
- admin-only endpoints protected by `ADMIN_API_KEY`

Endpoints:

```bash
curl -H "x-admin-api-key: $ADMIN_API_KEY" http://localhost:8000/api/analytics/summary
curl -H "x-admin-api-key: $ADMIN_API_KEY" http://localhost:8000/api/analytics/recent
```

Vercel Analytics can be enabled with `NEXT_PUBLIC_VERCEL_ANALYTICS=true`. Plausible is optional via `PLAUSIBLE_DOMAIN`.

## Deployment

Frontend:

- Deploy `frontend/` to Vercel.
- Set `NEXT_PUBLIC_BACKEND_URL`.
- Vercel Analytics is enabled by `NEXT_PUBLIC_VERCEL_ANALYTICS=true`.

Backend:

- Use `backend/app/deployment/Dockerfile.backend` for Docker/Fly.
- Use `backend/app/deployment/render.yaml` for Render.
- Use `backend/app/deployment/railway.toml` for Railway.
- On Render Free, use Supabase Postgres and Supabase Storage because local files are ephemeral.
- Persist `data/`, `outputs/`, and vector indexes on durable storage for paid/container deployments.
- Move from SQLite to managed PostgreSQL by changing `DATABASE_URL`.

MatterGen:

- Run as a separate GPU worker on local workstation, HPC, Modal, RunPod, or similar.
- Set `MATTERGEN_WORKER_URL` and `MATTERGEN_API_KEY`.
- Do not assume ordinary serverless CPU hosting can run MatterGen.

## Tests

```bash
pip install -r backend/requirements.txt
pytest backend/tests
```

Frontend:

```bash
cd frontend
npm install
npm run typecheck
npm run build
```

## Current Limitations

- Descriptor extraction and FBS-PM generation require OpenAI SDK/model access.
- MatterGen execution requires an installed local package/checkpoints/GPU or a remote worker.
- Public API sources are metadata-only and should be rate-limit aware.
- Time-split validation is implemented as a backend metric scaffold and should be extended with labelled later-literature comparisons.
- Frontend typechecking/building requires Node, which must be installed separately.
