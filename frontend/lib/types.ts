export type ScoreMap = Record<string, number>;

export interface Scope {
  scope_id: string;
  title: string;
  description: string;
  included_domains: string[];
  included_material_classes: string[];
  included_device_families: string[];
  included_mechanisms: string[];
  included_property_types: string[];
}

export interface EvidenceChunk {
  evidence_id: string;
  title: string;
  authors: string[];
  year?: number;
  doi?: string;
  source_type: string;
  page?: number;
  section?: string;
  snippet: string;
  relevance_score: number;
}

export interface LiteratureResult {
  title: string;
  authors: string[];
  year?: number;
  doi?: string;
  url?: string;
  source: string;
  abstract?: string;
  extra?: Record<string, unknown>;
}

export interface IngestionStatus {
  documents: number;
  evidence_chunks: number;
  application_nodes?: number;
}

export interface LiteratureIngestSummary extends IngestionStatus {
  documents_added: number;
  evidence_chunks_added: number;
  skipped: number;
}

export interface ApplicationNode {
  node_id: string;
  label: string;
  application_text: string;
  domain: string;
  function: string;
  operating_frequency_or_wavelength?: string;
  device_type?: string;
  physical_em_mechanism?: string;
  material_class?: string;
  material_names: string[];
  em_property_requirements: string[];
  evidence_ids: string[];
  year?: number;
  confidence: number;
  coordinates?: [number, number];
  cluster_id?: string;
  evidence_count: number;
}

export interface ApplicationCluster {
  cluster_id: string;
  label: string;
  summary: string;
  node_ids: string[];
  centroid: [number, number];
  domains: string[];
  mechanisms: string[];
  material_classes: string[];
  evidence_count: number;
}

export interface Gap {
  gap_id: string;
  scope_id: string;
  title: string;
  coordinates: [number, number];
  nearby_cluster_ids: string[];
  nearby_application_ids: string[];
  missing_descriptor_combination: Record<string, unknown>;
  boundary_descriptors: Record<string, string[]>;
  pseudo_application_hypotheses: string[];
  novelty_score: number;
  feasibility_score: number;
  boundary_evidence_score: number;
  neighbour_diversity_score: number;
  mattergen_compatibility_score: number;
  uncertainty_score: number;
  overall_gap_score: number;
  explanation: string;
}

export interface ApplicationSpace {
  build: {
    build_id: string;
    scope_id: string;
    reducer: string;
    clusterer: string;
    node_count: number;
    cluster_count: number;
    created_at: string;
  };
  nodes: ApplicationNode[];
  clusters: ApplicationCluster[];
  gaps: Gap[];
}

export interface PropertyRequirement {
  property_name: string;
  property_category: string;
  desired_direction: string;
  target_range_or_qualitative_requirement: string;
  frequency_or_wavelength_context?: string;
  why_required: string;
  measurement_method_or_proxy?: string;
  criticality: string;
  mattergen_direct_support: "supported" | "proxy_only" | "unsupported";
}

export interface MaterialCandidate {
  candidate_id: string;
  material: string;
  material_class: string;
  role_in_device: string;
  matched_em_properties: string[];
  missing_or_uncertain_properties: string[];
  evidence_strength: number;
  validation_status: string;
  source: string;
  confidence: number;
  next_validation_step: string;
}

export interface Pathway {
  pathway_id: string;
  gap_id: string;
  title: string;
  pathway_type: string;
  summary: string;
  pseudo_application: string;
  function: string;
  behaviour_or_mechanism: string;
  structure_or_device_realization: string;
  material_property_envelope: PropertyRequirement[];
  candidate_materials: MaterialCandidate[];
  mattergen_constraints?: {
    pathway_id: string;
    compatible_constraints: Record<string, unknown>;
    unsupported_em_properties: PropertyRequirement[];
    compatibility_score: number;
    notes: string[];
  };
  evidence_ids: string[];
  risks: string[];
  contradictions: string[];
  uncertainty: string;
  validation_status: string;
  scores: ScoreMap;
}

export interface MatterGenStatus {
  status: string;
  mode: string;
  path: string;
  importable: boolean;
  checkpoints_found: boolean;
  gpu_available: boolean;
  worker_configured: boolean;
  python_compatible: boolean;
  details: string[];
}

export interface EvaluationRun {
  run_id: string;
  mode: string;
  created_at: string;
  metrics: { name: string; value: number; details: Record<string, unknown> }[];
  warnings: string[];
}

export type HPCJobType =
  | "mattergen_generation"
  | "mattergen_validation"
  | "large_embedding_index_build"
  | "bulk_pdf_processing"
  | "dft_validation_placeholder"
  | "em_simulation_placeholder"
  | "custom_user_job_placeholder";

export type HPCJobStatus =
  | "created"
  | "transferring_inputs"
  | "submitted"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "retrieving_outputs"
  | "output_retrieved"
  | "unknown";

export interface HPCStatus {
  enabled: boolean;
  configured: boolean;
  mode: string;
  safe_authentication: boolean;
  host_configured: boolean;
  username_configured: boolean;
  workdir_configured: boolean;
  ssh_key_configured: boolean;
  ssh_agent_available: boolean;
  strict_host_key_checking: boolean;
  scheduler: string;
  scheduler_configured: boolean;
  mattergen_hpc_env_configured: boolean;
  supported_job_types: HPCJobType[];
  warnings: string[];
}

export interface HPCCheckResult {
  ok: boolean;
  status: string;
  message: string;
  details: string[];
}

export interface HPCJob {
  job_id: string;
  job_type: HPCJobType;
  status: HPCJobStatus;
  pathway_id?: string;
  slurm_job_id?: string;
  created_at: string;
  updated_at: string;
  input_ref?: string;
  output_ref?: string;
  log_excerpt: string;
  output_files: string[];
  candidates: MaterialCandidate[];
  error?: string;
}
