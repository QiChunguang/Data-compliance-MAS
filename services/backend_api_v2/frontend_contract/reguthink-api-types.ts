export type CaseGrade = "A" | "B" | "C" | "D" | "F";

export interface BoundaryFlags {
  not_production_ready: boolean;
  not_source_backed_pass: boolean;
  not_human_reviewed: boolean;
  prototype_context: boolean;
  business_case_files_available: boolean;
  business_evidence_files_available: boolean;
  local_neural_reranker_default_enabled: boolean;
  local_neural_reranker_status: "diagnostic_only" | string;
  bge_m3_status: "partially_effective" | "effective" | string;
  full18_mode: string;
}

export interface CaseBaselineRow {
  case_id: string;
  final_score: number;
  programmatic_score: number;
  llm_score: number;
  grade: CaseGrade;
  ge_70: boolean;
  bge_m3_status: string;
  main_issue: string;
}

export interface BaselineStatusResponse {
  phase: string;
  baseline_phase: string;
  authoritative_validation_phase: string;
  validation_status: string;
  full18_completed: string;
  strict_autojudge_completed: string;
  real_llm_judge_completed: string;
  case_count_score_ge_70: string;
  score_mean: number;
  score_min: number;
  score_max: number;
  boundary_flags: BoundaryFlags;
  immutability_rules: Record<string, boolean>;
  paths: Record<string, string>;
  file_status: Record<string, unknown>;
  warnings: string[];
}

export interface CaseListResponse {
  case_count: number;
  case_count_score_ge_70: number;
  cases: CaseBaselineRow[];
  warning: string;
}

export interface CaseArtifactsResponse {
  case_id: string;
  case_baseline: CaseBaselineRow | null;
  case_dir: string;
  case_dir_exists: boolean;
  boundary_flags: BoundaryFlags;
  json_artifacts: Record<string, unknown>;
  text_artifacts: Record<string, string | null>;
  file_status: Array<{ path: string; exists: boolean; size_bytes?: number | null }>;
  missing_files: string[];
  frontend_display_advice: string[];
}

export interface RunCaseRequest {
  case_id: string;
  dry_run: boolean;
  runtime_profile?: string;
}

export interface RunCaseResponse {
  ok: boolean;
  mode?: string;
  message: string;
  planned_execution?: Record<string, unknown>;
  allowed_case_ids?: string[];
}
