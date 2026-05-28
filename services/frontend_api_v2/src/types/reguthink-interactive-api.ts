export type AssessmentType =
  | "data_transaction_compliance"
  | "data_flow_security_review"
  | "cross_border_data_transfer"
  | "pipl_personal_information_protection"
  | "general_data_compliance_diagnostic";

export type ConversationStatus = "active" | "archived";
export type MessageRole = "user" | "assistant" | "system" | "tool";
export type RuntimeMode =
  | "chat"
  | "dry_run"
  | "controlled_runtime"
  | "uploaded_material_runtime"
  | "full_chain_runtime";
export type JobStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

export interface Conversation {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  assessment_type: AssessmentType;
  status: ConversationStatus;
  message_count: number;
  file_count: number;
}

export interface Message {
  message_id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  attachments: string[];
  run_id?: string | null;
  metadata: Record<string, unknown>;
}

export interface UploadedFile {
  file_id: string;
  conversation_id: string;
  original_filename: string;
  stored_path: string;
  display_path: string;
  mime_type?: string | null;
  size_bytes: number;
  sha256: string;
  uploaded_at: string;
  parse_status: string;
  text_preview?: string | null;
  extraction_warning?: string | null;
}

export interface AssessmentTypeInfo {
  assessment_type: AssessmentType;
  label: string;
  description: string;
}

export interface RuntimeJob {
  job_id: string;
  conversation_id: string;
  assessment_type: AssessmentType;
  status: JobStatus;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  progress: number;
  current_stage: string;
  input_files: string[];
  user_prompt: string;
  result_artifacts: Record<string, string>;
  error_message?: string | null;
  boundary_flags: Record<string, unknown>;
  runtime_mode: RuntimeMode;
}

export interface RuntimeEvent {
  event_id: string;
  job_id: string;
  event_type: string;
  stage: string;
  message: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface CreateConversationRequest {
  title?: string;
  assessment_type?: AssessmentType;
}

export interface CreateMessageRequest {
  content: string;
  attachments?: string[];
}

export interface UploadFileResponse extends UploadedFile {}

export interface RunAssessmentRequest {
  assessment_type: AssessmentType;
  user_prompt: string;
  file_ids: string[];
  runtime_mode: RuntimeMode;
}

export interface RunAssessmentResponse {
  job_id: string;
  status: JobStatus;
  message: string;
}

export interface JobStatusResponse extends RuntimeJob {}

export interface JobEventsResponse {
  events: RuntimeEvent[];
}

export interface ConversationJobsResponse {
  jobs: RuntimeJob[];
}

export interface ConversationMemoryResponse {
  conversation_id: string;
  memory_dir: string;
  messages_path: string;
  summary: Record<string, unknown>;
  latest_context_pack: Record<string, unknown>;
}

export interface AssessmentIntent {
  detected_type?: string;
  confidence?: string;
  matched_keywords?: string[];
  suggested_types?: Array<Record<string, unknown>>;
  recommendation?: string;
}

export interface UploadedMaterialIntake {
  file_count?: number;
  file_summaries?: Array<Record<string, unknown>>;
  parties?: string[];
  data_type?: string[];
  transfer_direction?: string[];
  cross_border_indicators?: string[];
  personal_information_indicators?: string[];
  sensitive_pi_indicators?: string[];
  transaction_context?: string[];
  missing_information?: string[];
  boundary_warnings?: string[];
}

export interface ChatRequest {
  content: string;
  message?: string;
  assessment_type?: AssessmentType | null;
  file_ids?: string[];
  auto_run_assessment?: boolean;
  runtime_mode?: RuntimeMode;
  action?: "send_message" | "run_full_chain_report" | string;
  rag_enabled?: boolean;
  autojudge_enabled?: boolean;
}

export interface ChatResponse {
  user_message: Message;
  assistant_message: Message;
  intent: AssessmentIntent;
  uploaded_material_intake: UploadedMaterialIntake;
  suggested_next_actions: string[];
  job_id: string | null;
  boundary_flags: Record<string, unknown>;
  runtime_mode_effective?: RuntimeMode;
  auto_judge_expected?: boolean;
  full_chain_runtime_supported?: boolean;
  runtime_limitations?: string[];
  recommended_followups?: string[];
  chat_metadata?: Record<string, unknown>;
  full_chain_job_created?: boolean;
  report_generated?: boolean;
  rag_used?: boolean;
  llm_used?: boolean;
  uploaded_file_context_used?: boolean;
}

export type JobArtifactsResponse = Record<string, unknown>;

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  labels?: string[];
  properties_summary?: Record<string, unknown>;
  source_id?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  properties_summary?: Record<string, unknown>;
}

export interface GraphResponse {
  status: "ok" | "graph_unavailable" | "graph_empty" | "not_found" | string;
  graph_available?: boolean;
  graph_empty?: boolean;
  reason?: string;
  message?: string;
  graph_version?: string;
  database_masked?: string;
  readonly?: boolean;
  node_counts_by_label?: Record<string, number>;
  edge_counts_by_type?: Record<string, number>;
  nodes?: GraphNode[];
  edges?: GraphEdge[];
  labels?: string[];
  relationship_types?: string[];
  node?: GraphNode;
}
