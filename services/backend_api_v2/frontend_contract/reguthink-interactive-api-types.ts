export type AssessmentType =
  | "data_transaction_compliance"
  | "data_flow_security_review"
  | "cross_border_data_transfer"
  | "pipl_personal_information_protection"
  | "general_data_compliance_diagnostic";

export type ConversationStatus = "active" | "archived";
export type MessageRole = "user" | "assistant" | "system" | "tool";
export type RuntimeMode = "dry_run" | "controlled_runtime";
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
