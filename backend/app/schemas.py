from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class EvidenceSupport(str, Enum):
    evidence_supported = "evidence-supported"
    analogy_supported = "analogy-supported"
    speculative = "speculative"
    unsupported = "unsupported"


class ValidationStatus(str, Enum):
    unvalidated = "unvalidated"
    literature_supported = "literature-supported"
    ml_predicted = "ML-predicted"
    dft_pending = "DFT-pending"
    dft_validated = "DFT-validated"
    em_simulation_pending = "EM-simulation-pending"
    em_simulation_validated = "EM-simulation-validated"
    experimentally_validated = "experimentally-validated"
    rejected = "rejected"


class MatterGenDirectSupport(str, Enum):
    supported = "supported"
    proxy_only = "proxy_only"
    unsupported = "unsupported"


class Scope(BaseModel):
    scope_id: str
    title: str
    description: str
    included_domains: List[str] = Field(default_factory=list)
    included_material_classes: List[str] = Field(default_factory=list)
    included_device_families: List[str] = Field(default_factory=list)
    included_mechanisms: List[str] = Field(default_factory=list)
    included_property_types: List[str] = Field(default_factory=list)
    excluded_domains: List[str] = Field(default_factory=list)
    excluded_material_classes: List[str] = Field(default_factory=list)
    mattergen_compatibility_notes: List[str] = Field(default_factory=list)
    validation_methods: List[str] = Field(default_factory=list)
    default_search_queries: List[str] = Field(default_factory=list)
    descriptor_weights: Dict[str, float] = Field(default_factory=dict)


class Document(BaseModel):
    document_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    source_type: str = "local"
    source_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceChunk(BaseModel):
    evidence_id: str
    document_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    source_type: str
    source_path: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    text: str
    snippet: str
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LiteratureResult(BaseModel):
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    source: str
    abstract: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class LiteratureSearchRequest(BaseModel):
    query: str
    limit: int = 20


class LiteratureIngestRequest(BaseModel):
    results: List[LiteratureResult]


class LiteratureIngestAndExtractRequest(LiteratureIngestRequest):
    scope_id: str = "electromagnetic_functional_materials"
    limit: int = 50


class DescriptorExtractionRequest(BaseModel):
    evidence_ids: List[str] = Field(default_factory=list)


def coerce_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        separators = ("\n", ";", "|")
        if any(separator in text for separator in separators):
            parts = [part.strip(" -\t\r\n") for part in text.replace("|", "\n").replace(";", "\n").splitlines()]
            return [part for part in parts if part]
        return [text]
    if isinstance(value, (list, tuple, set)):
        items: List[str] = []
        for item in value:
            items.extend(coerce_string_list(item))
        return items
    return [str(value)]


def coerce_coordinates(value: Any) -> Optional[List[float]]:
    if value in (None, "", []):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped in {"[]", "null", "None"}:
            return None
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                return coerce_coordinates(json.loads(stripped))
            except Exception:
                return None
        parts = [part.strip() for part in stripped.replace(";", ",").split(",")]
        if len(parts) >= 2:
            try:
                return [float(parts[0]), float(parts[1])]
            except ValueError:
                return None
        return None
    if isinstance(value, dict):
        x = value.get("x", value.get("0"))
        y = value.get("y", value.get("1"))
        if x is None or y is None:
            return None
        try:
            return [float(x), float(y)]
        except (TypeError, ValueError):
            return None
    if isinstance(value, (list, tuple)):
        if len(value) < 2:
            return None
        try:
            return [float(value[0]), float(value[1])]
        except (TypeError, ValueError):
            return None
    return None


class ApplicationNode(BaseModel):
    node_id: str
    label: str
    application_text: str
    domain: str
    function: str
    stimulus: Optional[str] = None
    response: Optional[str] = None
    operating_frequency_or_wavelength: Optional[str] = None
    operating_environment: Optional[str] = None
    device_type: Optional[str] = None
    device_architecture: Optional[str] = None
    physical_em_mechanism: Optional[str] = None
    material_class: Optional[str] = None
    material_names: List[str] = Field(default_factory=list)
    em_property_requirements: List[str] = Field(default_factory=list)
    non_em_constraints: List[str] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    confidence: float = 0.0
    coordinates: Optional[List[float]] = None
    cluster_id: Optional[str] = None
    evidence_count: int = 0

    @field_validator(
        "material_names",
        "em_property_requirements",
        "non_em_constraints",
        "source_ids",
        "evidence_ids",
        mode="before",
    )
    @classmethod
    def coerce_string_lists(cls, value: Any) -> List[str]:
        return coerce_string_list(value)

    @field_validator("coordinates", mode="before")
    @classmethod
    def coerce_coordinates_field(cls, value: Any) -> Optional[List[float]]:
        return coerce_coordinates(value)


class ApplicationCluster(BaseModel):
    cluster_id: str
    label: str
    summary: str
    node_ids: List[str] = Field(default_factory=list)
    centroid: List[float] = Field(default_factory=lambda: [0.0, 0.0])
    domains: List[str] = Field(default_factory=list)
    mechanisms: List[str] = Field(default_factory=list)
    material_classes: List[str] = Field(default_factory=list)
    evidence_count: int = 0


class ApplicationSpaceBuild(BaseModel):
    build_id: str
    scope_id: str
    random_seed: int
    reducer: str
    clusterer: str
    density_method: str
    node_count: int
    cluster_count: int
    created_at: str
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ApplicationSpaceResponse(BaseModel):
    build: ApplicationSpaceBuild
    nodes: List[ApplicationNode]
    clusters: List[ApplicationCluster]
    gaps: List["Gap"] = Field(default_factory=list)


class Gap(BaseModel):
    gap_id: str
    scope_id: str
    title: str
    coordinates: List[float]
    nearby_cluster_ids: List[str] = Field(default_factory=list)
    nearby_application_ids: List[str] = Field(default_factory=list)
    missing_descriptor_combination: Dict[str, Any] = Field(default_factory=dict)
    boundary_descriptors: Dict[str, Any] = Field(default_factory=dict)
    pseudo_application_hypotheses: List[str] = Field(default_factory=list)
    novelty_score: float
    feasibility_score: float
    boundary_evidence_score: float
    neighbour_diversity_score: float
    mattergen_compatibility_score: float
    uncertainty_score: float
    overall_gap_score: float
    explanation: str


class PropertyRequirement(BaseModel):
    property_name: str
    property_category: str
    desired_direction: str
    target_range_or_qualitative_requirement: str
    frequency_or_wavelength_context: Optional[str] = None
    temperature_context: Optional[str] = None
    why_required: str
    measurement_method_or_proxy: Optional[str] = None
    criticality: str = "medium"
    evidence_ids: List[str] = Field(default_factory=list)
    mattergen_direct_support: MatterGenDirectSupport = MatterGenDirectSupport.unsupported
    validation_method: Optional[str] = None


class MaterialCandidate(BaseModel):
    candidate_id: str
    material: str
    material_class: str
    role_in_device: str
    matched_em_properties: List[str] = Field(default_factory=list)
    missing_or_uncertain_properties: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    evidence_strength: float = 0.0
    validation_status: ValidationStatus = ValidationStatus.unvalidated
    source: str = "literature"
    confidence: float = 0.0
    next_validation_step: str = "Review supporting literature and run property validation."


class MatterGenConstraintSet(BaseModel):
    pathway_id: str
    compatible_constraints: Dict[str, Any] = Field(default_factory=dict)
    unsupported_em_properties: List[PropertyRequirement] = Field(default_factory=list)
    compatibility_score: float = 0.0
    notes: List[str] = Field(default_factory=list)


class FBSPMPathway(BaseModel):
    pathway_id: str
    gap_id: str
    title: str
    pathway_type: EvidenceSupport
    summary: str
    pseudo_application: str
    function: str
    behaviour_or_mechanism: str
    structure_or_device_realization: str
    device_architecture: Optional[str] = None
    operating_frequency_or_wavelength_range: Optional[str] = None
    material_property_envelope: List[PropertyRequirement] = Field(default_factory=list)
    candidate_materials: List[MaterialCandidate] = Field(default_factory=list)
    mattergen_constraints: Optional[MatterGenConstraintSet] = None
    evidence_ids: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    uncertainty: str
    validation_status: ValidationStatus = ValidationStatus.unvalidated
    scores: Dict[str, float] = Field(default_factory=dict)


class MatterGenStatus(BaseModel):
    status: str
    mode: str
    path: str
    importable: bool
    checkpoints_found: bool
    gpu_available: bool
    worker_configured: bool
    python_compatible: bool
    details: List[str] = Field(default_factory=list)


class MatterGenJob(BaseModel):
    job_id: str
    pathway_id: str
    status: str
    constraint_set: MatterGenConstraintSet
    output_dir: str
    created_at: str
    updated_at: str
    candidates: List[MaterialCandidate] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class HPCJobType(str, Enum):
    mattergen_generation = "mattergen_generation"
    mattergen_validation = "mattergen_validation"
    large_embedding_index_build = "large_embedding_index_build"
    bulk_pdf_processing = "bulk_pdf_processing"
    dft_validation_placeholder = "dft_validation_placeholder"
    em_simulation_placeholder = "em_simulation_placeholder"
    custom_user_job_placeholder = "custom_user_job_placeholder"


class HPCJobStatus(str, Enum):
    created = "created"
    transferring_inputs = "transferring_inputs"
    submitted = "submitted"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    retrieving_outputs = "retrieving_outputs"
    output_retrieved = "output_retrieved"
    unknown = "unknown"


class HPCStatus(BaseModel):
    enabled: bool
    configured: bool
    mode: str
    queue_only: bool = False
    safe_authentication: bool
    host_configured: bool
    username_configured: bool
    workdir_configured: bool
    ssh_key_configured: bool
    ssh_agent_available: bool
    strict_host_key_checking: bool
    scheduler: str = "slurm"
    scheduler_configured: bool
    mattergen_hpc_env_configured: bool
    supported_job_types: List[HPCJobType] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class HPCCheckResult(BaseModel):
    ok: bool
    status: str
    message: str
    details: List[str] = Field(default_factory=list)


class HPCJobCreateRequest(BaseModel):
    job_type: HPCJobType
    pathway_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class HPCJob(BaseModel):
    job_id: str
    job_type: HPCJobType
    status: HPCJobStatus
    pathway_id: Optional[str] = None
    slurm_job_id: Optional[str] = None
    created_at: str
    updated_at: str
    input_ref: Optional[str] = None
    remote_workdir: Optional[str] = None
    local_workdir: Optional[str] = None
    output_ref: Optional[str] = None
    log_excerpt: str = ""
    output_files: List[str] = Field(default_factory=list)
    candidates: List[MaterialCandidate] = Field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricResult(BaseModel):
    name: str
    value: float
    details: Dict[str, Any] = Field(default_factory=dict)


class EvaluationRun(BaseModel):
    run_id: str
    scope_id: str
    mode: str
    created_at: str
    metrics: List[MetricResult] = Field(default_factory=list)
    artifacts: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class BaselineRunRequest(BaseModel):
    mode: str
    scope_id: str = "electromagnetic_functional_materials"
    gap_id: Optional[str] = None
    query: Optional[str] = None


class AnalyticsSummary(BaseModel):
    visits_today: int
    unique_anonymous_visitors_today: int
    average_request_time_ms: float
    errors_by_endpoint: Dict[str, int] = Field(default_factory=dict)
    top_routes: List[Dict[str, Any]] = Field(default_factory=list)
    top_referrers: List[Dict[str, Any]] = Field(default_factory=list)
    deployment_env: str


class ReportRecord(BaseModel):
    report_id: str
    gap_id: str
    markdown_path: str
    json_path: str
    evidence_csv_path: str
    created_at: str


ApplicationSpaceResponse.update_forward_refs()
