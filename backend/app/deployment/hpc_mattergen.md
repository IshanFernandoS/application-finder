# MatterGen on QMUL Apocrita HPC

The local Mac setup can install and import MatterGen, but real generation should run on a CUDA GPU worker. QMUL Apocrita uses SSH login and Slurm batch jobs, so the project provides interactive SSH/Slurm helper scripts rather than storing passwords, passcodes, or university credentials.

Application Finder also includes an admin-only backend HPC worker API at `/api/hpc/*`. It uses the same safety boundary: SSH key/agent authentication, `rsync` for file transfer, and Slurm `sbatch`/`squeue`/`sacct`/`scancel` for scheduled jobs. The web backend must not run heavy compute directly or host itself on the login node.

## Prepare Remote Workspace

```bash
scripts/hpc_mattergen_prepare.sh
```

This creates a remote workspace, syncs the repository, writes a remote bootstrap script, and prints the command to run it. The bootstrap script installs MatterGen and pulls Git LFS checkpoints on the HPC side.

## Bootstrap MatterGen on HPC

Run the printed command, for example:

```bash
ssh -A "$HPC_USERNAME@$HPC_HOST" \
  'PROJECT_DIR=$HPC_WORKDIR bash $HPC_WORKDIR/bootstrap_mattergen.sh'
```

## Submit a GPU Job

```bash
scripts/hpc_mattergen_submit.sh PATHWAY_ID outputs/pathway_constraints.json
```

Environment variables:

- `HPC_SLURM_PARTITION`, default `gpushort` in the legacy helper for quick MatterGen runs
- `HPC_GPU_REQUEST`, default `gpu:1`
- `HPC_CPUS_PER_TASK`, default `8`
- `HPC_MEM`, default `32G`
- `HPC_TIME_LIMIT`, default `01:00:00`
- `HPC_WORKDIR`, default `/data/scratch/$HPC_USERNAME/gap2material-em`

The legacy helpers still accept old aliases such as `HPC_USER`, `HPC_KEY`, `HPC_PROJECT_DIR`, `HPC_PARTITION`, `HPC_GPUS`, `HPC_CPUS`, and `HPC_TIME`, but new deployments should use the variables above.

The submitted Slurm script verifies CUDA, reads the exported constraint JSON, selects a compatible pretrained MatterGen mode where possible, and runs `mattergen-generate`. It currently maps:

- `chemical_system` + `energy_above_hull` -> `chemical_system_energy_above_hull`
- `chemical_system` -> `chemical_system`
- `magnetic_density` -> `dft_mag_density`
- `band_gap` -> `dft_band_gap`
- `bulk_modulus` -> `ml_bulk_modulus`
- otherwise -> `mattergen_base`

Properties that MatterGen does not directly support remain validation requirements in Application Finder.

## Fetch Outputs

```bash
scripts/hpc_mattergen_fetch.sh PATHWAY_ID
```

Fetched files are placed under `outputs/mattergen/PATHWAY_ID/`.

## General HPC Worker Helpers

The generalized helper scripts use the `HPC_*` environment variables documented in `.env.example`:

```bash
scripts/hpc/submit_mattergen_job.sh PATHWAY_ID outputs/pathway_constraints.json
scripts/hpc/check_job_status.sh SLURM_JOB_ID
scripts/hpc/retrieve_job_outputs.sh HPC_JOB_ID
```

The admin API supports:

- `mattergen_generation`
- `mattergen_validation`
- `large_embedding_index_build`
- `bulk_pdf_processing`
- `dft_validation_placeholder`
- `em_simulation_placeholder`
- `custom_user_job_placeholder`

## Security

Do not store HPC passwords, passcodes, or one-time tokens in `.env`, scripts, job files, shell history, or notebooks. Authenticate interactively through SSH.

Check and follow your institution's HPC policy before enabling the worker.
