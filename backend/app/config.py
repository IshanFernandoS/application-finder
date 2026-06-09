from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


ROOT_DIR = Path(__file__).resolve().parents[2]


def _load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: Optional[str]
    openai_model: str
    openai_embedding_model: str
    semantic_scholar_api_key: Optional[str]
    unpaywall_email: str
    data_dir: Path
    output_dir: Path
    database_url: str
    vector_backend: str
    object_storage_backend: str
    supabase_url: Optional[str]
    supabase_service_role_key: Optional[str]
    supabase_storage_bucket: str
    supabase_signed_url_ttl_seconds: int
    enable_online_metadata: bool
    enable_openai_reasoning: bool
    enable_mattergen: bool
    mattergen_mode: str
    mattergen_path: Path
    mattergen_worker_url: Optional[str]
    mattergen_api_key: Optional[str]
    deployment_env: str
    frontend_url: str
    backend_url: str
    enable_analytics: bool
    analytics_provider: str
    plausible_domain: Optional[str]
    access_logging_enabled: bool
    access_log_hash_salt: str
    access_log_retention_days: int
    access_log_store_raw_ip: bool
    access_log_store_user_agent_raw: bool
    access_log_geoip: bool
    admin_api_key: Optional[str]
    hpc_enabled: bool
    hpc_mode: str
    hpc_host: Optional[str]
    hpc_username: Optional[str]
    hpc_ssh_key_path: Optional[Path]
    hpc_workdir: Optional[str]
    hpc_slurm_partition: Optional[str]
    hpc_slurm_account: Optional[str]
    hpc_gpu_request: Optional[str]
    hpc_time_limit: str
    hpc_cpus_per_task: int
    hpc_mem: str
    hpc_python_module: Optional[str]
    hpc_mattergen_env: Optional[str]
    hpc_rsync_extra_args: str
    hpc_strict_host_key_checking: bool
    hpc_known_hosts_path: Optional[Path]

    @classmethod
    def from_env(cls) -> "Settings":
        env_file = _load_env_file(ROOT_DIR / ".env")
        for key, value in env_file.items():
            os.environ.setdefault(key, value)

        data_dir = Path(os.getenv("DATA_DIR", "data"))
        output_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
        mattergen_path = Path(os.getenv("MATTERGEN_PATH", "tools/mattergen"))

        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY") or None,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
            semantic_scholar_api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY") or None,
            unpaywall_email=os.getenv("UNPAYWALL_EMAIL", "h.i.s.fernando@qmul.ac.uk"),
            data_dir=(ROOT_DIR / data_dir).resolve() if not data_dir.is_absolute() else data_dir,
            output_dir=(ROOT_DIR / output_dir).resolve() if not output_dir.is_absolute() else output_dir,
            database_url=os.getenv("DATABASE_URL", "sqlite:///data/gap2material_em.db"),
            vector_backend=os.getenv("VECTOR_BACKEND", "chroma"),
            object_storage_backend=os.getenv("OBJECT_STORAGE_BACKEND", "local"),
            supabase_url=os.getenv("SUPABASE_URL") or None,
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") or None,
            supabase_storage_bucket=os.getenv("SUPABASE_STORAGE_BUCKET", "gap2material-artifacts"),
            supabase_signed_url_ttl_seconds=int(os.getenv("SUPABASE_SIGNED_URL_TTL_SECONDS", "604800")),
            enable_online_metadata=env_bool("ENABLE_ONLINE_METADATA", True),
            enable_openai_reasoning=env_bool("ENABLE_OPENAI_REASONING", True),
            enable_mattergen=env_bool("ENABLE_MATTERGEN", True),
            mattergen_mode=os.getenv("MATTERGEN_MODE", "local"),
            mattergen_path=(ROOT_DIR / mattergen_path).resolve() if not mattergen_path.is_absolute() else mattergen_path,
            mattergen_worker_url=os.getenv("MATTERGEN_WORKER_URL") or None,
            mattergen_api_key=os.getenv("MATTERGEN_API_KEY") or None,
            deployment_env=os.getenv("DEPLOYMENT_ENV", "local"),
            frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
            backend_url=os.getenv("BACKEND_URL", "http://localhost:8000"),
            enable_analytics=env_bool("ENABLE_ANALYTICS", True),
            analytics_provider=os.getenv("ANALYTICS_PROVIDER", "internal"),
            plausible_domain=os.getenv("PLAUSIBLE_DOMAIN") or None,
            access_logging_enabled=env_bool("ACCESS_LOGGING_ENABLED", True),
            access_log_hash_salt=os.getenv("ACCESS_LOG_HASH_SALT", ""),
            access_log_retention_days=int(os.getenv("ACCESS_LOG_RETENTION_DAYS", "30")),
            access_log_store_raw_ip=env_bool("ACCESS_LOG_STORE_RAW_IP", False),
            access_log_store_user_agent_raw=env_bool("ACCESS_LOG_STORE_USER_AGENT_RAW", False),
            access_log_geoip=env_bool("ACCESS_LOG_GEOIP", False),
            admin_api_key=os.getenv("ADMIN_API_KEY") or None,
            hpc_enabled=env_bool("HPC_ENABLED", False),
            hpc_mode=os.getenv("HPC_MODE", "slurm_ssh"),
            hpc_host=os.getenv("HPC_HOST", "login.hpc.qmul.ac.uk") or None,
            hpc_username=os.getenv("HPC_USERNAME") or os.getenv("HPC_USER") or None,
            hpc_ssh_key_path=Path(os.getenv("HPC_SSH_KEY_PATH") or os.getenv("HPC_KEY", "")).expanduser()
            if (os.getenv("HPC_SSH_KEY_PATH") or os.getenv("HPC_KEY"))
            else None,
            hpc_workdir=os.getenv("HPC_WORKDIR") or os.getenv("HPC_PROJECT_DIR") or None,
            hpc_slurm_partition=os.getenv("HPC_SLURM_PARTITION") or os.getenv("HPC_PARTITION") or None,
            hpc_slurm_account=os.getenv("HPC_SLURM_ACCOUNT") or None,
            hpc_gpu_request=os.getenv("HPC_GPU_REQUEST") or (f"gpu:{os.getenv('HPC_GPUS')}" if os.getenv("HPC_GPUS") else None),
            hpc_time_limit=os.getenv("HPC_TIME_LIMIT") or os.getenv("HPC_TIME", "04:00:00"),
            hpc_cpus_per_task=int(os.getenv("HPC_CPUS_PER_TASK") or os.getenv("HPC_CPUS", "8")),
            hpc_mem=os.getenv("HPC_MEM", "32G"),
            hpc_python_module=os.getenv("HPC_PYTHON_MODULE") or None,
            hpc_mattergen_env=os.getenv("HPC_MATTERGEN_ENV") or None,
            hpc_rsync_extra_args=os.getenv("HPC_RSYNC_EXTRA_ARGS", ""),
            hpc_strict_host_key_checking=env_bool("HPC_STRICT_HOST_KEY_CHECKING", True),
            hpc_known_hosts_path=Path(os.getenv("HPC_KNOWN_HOSTS_PATH", "")).expanduser()
            if os.getenv("HPC_KNOWN_HOSTS_PATH")
            else None,
        )

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def supabase_storage_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key and self.supabase_storage_bucket)

    @property
    def hpc_configured(self) -> bool:
        return bool(self.hpc_enabled and self.hpc_host and self.hpc_username and self.hpc_workdir)


settings = Settings.from_env()
