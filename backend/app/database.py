from __future__ import annotations

from pathlib import Path
from typing import Iterator

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy import JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

from .config import ROOT_DIR, settings


def _resolve_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return url
    path = Path(url[len(prefix) :])
    if not path.is_absolute():
        path = ROOT_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return prefix + str(path)


engine = create_engine(
    _resolve_database_url(settings.database_url),
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class ScopeRecord(Base):
    __tablename__ = "scopes"
    scope_id = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DocumentRecord(Base):
    __tablename__ = "documents"
    document_id = Column(String, primary_key=True)
    doi = Column(String, index=True)
    title = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EvidenceRecord(Base):
    __tablename__ = "evidence_chunks"
    evidence_id = Column(String, primary_key=True)
    document_id = Column(String, index=True, nullable=False)
    text = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ApplicationNodeRecord(Base):
    __tablename__ = "application_nodes"
    node_id = Column(String, primary_key=True)
    scope_id = Column(String, index=True, nullable=False)
    cluster_id = Column(String, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ApplicationClusterRecord(Base):
    __tablename__ = "application_clusters"
    cluster_id = Column(String, primary_key=True)
    scope_id = Column(String, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ApplicationBuildRecord(Base):
    __tablename__ = "application_space_builds"
    build_id = Column(String, primary_key=True)
    scope_id = Column(String, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GapRecord(Base):
    __tablename__ = "gaps"
    gap_id = Column(String, primary_key=True)
    scope_id = Column(String, index=True, nullable=False)
    overall_gap_score = Column(Float, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PathwayRecord(Base):
    __tablename__ = "pathways"
    pathway_id = Column(String, primary_key=True)
    gap_id = Column(String, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CandidateRecord(Base):
    __tablename__ = "material_candidates"
    candidate_id = Column(String, primary_key=True)
    pathway_id = Column(String, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MatterGenJobRecord(Base):
    __tablename__ = "mattergen_jobs"
    job_id = Column(String, primary_key=True)
    pathway_id = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HPCJobRecord(Base):
    __tablename__ = "hpc_jobs"
    job_id = Column(String, primary_key=True)
    job_type = Column(String, index=True, nullable=False)
    status = Column(String, index=True, nullable=False)
    pathway_id = Column(String, index=True)
    slurm_job_id = Column(String, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EvaluationRunRecord(Base):
    __tablename__ = "evaluation_runs"
    run_id = Column(String, primary_key=True)
    scope_id = Column(String, index=True, nullable=False)
    mode = Column(String, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AccessLogRecord(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    route = Column(String, index=True, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(Integer, index=True, nullable=False)
    referrer_domain = Column(String)
    device_category = Column(String)
    browser_family = Column(String)
    visitor_hash = Column(String, index=True)
    session_hash = Column(String, index=True)
    request_duration_ms = Column(Float, nullable=False)
    deployment_env = Column(String)
    raw_ip = Column(String)
    raw_user_agent = Column(Text)


class ReportRecordModel(Base):
    __tablename__ = "reports"
    report_id = Column(String, primary_key=True)
    gap_id = Column(String, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
