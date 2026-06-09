from backend.app.schemas import HPCJobStatus
from backend.app.services.hpc_slurm_service import HPCSlurmService
from backend.app.services.hpc_worker_service import HPCWorkerService


def test_slurm_state_mapping():
    service = HPCSlurmService()
    assert service.map_slurm_state("PENDING") == HPCJobStatus.queued
    assert service.map_slurm_state("RUNNING") == HPCJobStatus.running
    assert service.map_slurm_state("COMPLETED") == HPCJobStatus.completed
    assert service.map_slurm_state("FAILED") == HPCJobStatus.failed
    assert service.map_slurm_state("CANCELLED") == HPCJobStatus.cancelled


def test_hpc_status_does_not_expose_secret_values():
    status = HPCWorkerService().status()
    data = status.model_dump()
    assert "hpc_ssh_key_path" not in data
    assert "supported_job_types" in data
