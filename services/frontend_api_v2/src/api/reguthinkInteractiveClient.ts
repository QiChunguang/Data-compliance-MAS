import type {
  AssessmentTypeInfo,
  ChatRequest,
  ChatResponse,
  Conversation,
  CreateConversationRequest,
  CreateMessageRequest,
  JobArtifactsResponse,
  JobEventsResponse,
  JobStatusResponse,
  ConversationJobsResponse,
  ConversationMemoryResponse,
  GraphResponse,
  Message,
  RunAssessmentRequest,
  RunAssessmentResponse,
  RuntimeEvent,
  UploadedFile,
} from "../types/reguthink-interactive-api";
import { REGUTHINK_API_BASE_URL } from "./reguthinkConfig";

export type InteractiveErrorKind =
  | "network"
  | "not_found"
  | "server"
  | "http"
  | "parse"
  | "stream"
  | "runtime_failed";

export class ReguThinkInteractiveError extends Error {
  kind: InteractiveErrorKind;
  status?: number;

  constructor(kind: InteractiveErrorKind, message: string, status?: number) {
    super(message);
    this.name = "ReguThinkInteractiveError";
    this.kind = kind;
    this.status = status;
  }
}

const API_BASE_URL = REGUTHINK_API_BASE_URL;

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (error) {
    throw new ReguThinkInteractiveError(
      "parse",
      error instanceof Error ? `JSON parse failure: ${error.message}` : "JSON parse failure",
      response.status,
    );
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
    });
  } catch (error) {
    throw new ReguThinkInteractiveError(
      "network",
      error instanceof Error ? `Backend down or network error: ${error.message}` : "Backend down or network error",
    );
  }

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    if (response.status === 404) {
      throw new ReguThinkInteractiveError("not_found", detail || "HTTP 404", response.status);
    }
    if (response.status >= 500) {
      throw new ReguThinkInteractiveError("server", detail || `HTTP ${response.status}`, response.status);
    }
    throw new ReguThinkInteractiveError("http", detail || `HTTP ${response.status}`, response.status);
  }

  return parseJson<T>(response);
}

export const reguthinkInteractiveClient = {
  baseUrl: API_BASE_URL,

  async getAssessmentTypes(): Promise<AssessmentTypeInfo[]> {
    const data = await request<{ assessment_types: AssessmentTypeInfo[] }>("/api/v1/assessment-types");
    return data.assessment_types;
  },

  createConversation(req: CreateConversationRequest = {}): Promise<Conversation> {
    return request<Conversation>("/api/v1/conversations", { method: "POST", body: JSON.stringify(req) });
  },

  async listConversations(): Promise<Conversation[]> {
    const data = await request<{ conversations: Conversation[] }>("/api/v1/conversations");
    return data.conversations;
  },

  getConversation(conversationId: string): Promise<Conversation> {
    return request<Conversation>(`/api/v1/conversations/${encodeURIComponent(conversationId)}`);
  },

  async getLatestJob(conversationId: string): Promise<JobStatusResponse | null> {
    const data = await request<{ job: JobStatusResponse | null }>(
      `/api/v1/conversations/${encodeURIComponent(conversationId)}/latest-job`,
    );
    return data.job;
  },

  async listConversationJobs(conversationId: string): Promise<JobStatusResponse[]> {
    const data = await request<ConversationJobsResponse>(
      `/api/v1/conversations/${encodeURIComponent(conversationId)}/jobs`,
    );
    return data.jobs;
  },

  getConversationMemory(conversationId: string): Promise<ConversationMemoryResponse> {
    return request<ConversationMemoryResponse>(`/api/v1/conversations/${encodeURIComponent(conversationId)}/memory`);
  },

  async getMessages(conversationId: string): Promise<Message[]> {
    const data = await request<{ messages: Message[] }>(
      `/api/v1/conversations/${encodeURIComponent(conversationId)}/messages`,
    );
    return data.messages;
  },

  sendMessage(conversationId: string, content: string, attachments: string[] = []): Promise<Message> {
    const req: CreateMessageRequest = { content, attachments };
    return request<Message>(`/api/v1/conversations/${encodeURIComponent(conversationId)}/messages`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  chat(conversationId: string, req: ChatRequest): Promise<ChatResponse> {
    return request<ChatResponse>(`/api/v1/conversations/${encodeURIComponent(conversationId)}/chat`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  uploadFile(conversationId: string, file: File): Promise<UploadedFile> {
    const form = new FormData();
    form.append("file", file);
    return request<UploadedFile>(`/api/v1/conversations/${encodeURIComponent(conversationId)}/files`, {
      method: "POST",
      body: form,
    });
  },

  async listFiles(conversationId: string): Promise<UploadedFile[]> {
    const data = await request<{ files: UploadedFile[] }>(
      `/api/v1/conversations/${encodeURIComponent(conversationId)}/files`,
    );
    return data.files;
  },

  getFile(fileId: string): Promise<UploadedFile> {
    return request<UploadedFile>(`/api/v1/files/${encodeURIComponent(fileId)}`);
  },

  runAssessment(conversationId: string, req: RunAssessmentRequest): Promise<RunAssessmentResponse> {
    return request<RunAssessmentResponse>(`/api/v1/conversations/${encodeURIComponent(conversationId)}/assessments/run`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  getJob(jobId: string): Promise<JobStatusResponse> {
    return request<JobStatusResponse>(`/api/v1/jobs/${encodeURIComponent(jobId)}`);
  },

  getJobEvents(jobId: string): Promise<JobEventsResponse> {
    return request<JobEventsResponse>(`/api/v1/jobs/${encodeURIComponent(jobId)}/events`);
  },

  async getJobArtifacts(jobId: string): Promise<JobArtifactsResponse> {
    const data = await request<{ job: unknown; artifacts: JobArtifactsResponse }>(`/api/v1/jobs/${encodeURIComponent(jobId)}/artifacts`);
    return data.artifacts ?? data;
  },

  artifactDownloadUrl(jobId: string, artifactName = "user_report.md"): string {
    return `${API_BASE_URL}/api/v1/jobs/${encodeURIComponent(jobId)}/artifacts/${encodeURIComponent(artifactName)}/download`;
  },

  cancelJob(jobId: string): Promise<JobStatusResponse> {
    return request<JobStatusResponse>(`/api/v1/jobs/${encodeURIComponent(jobId)}/cancel`, { method: "POST" });
  },

  graphHealth(): Promise<GraphResponse> {
    return request<GraphResponse>("/api/v1/graph/health");
  },

  graphOverview(): Promise<GraphResponse> {
    return request<GraphResponse>("/api/v1/graph/overview");
  },

  graphSchema(): Promise<GraphResponse> {
    return request<GraphResponse>("/api/v1/graph/schema");
  },

  graphSubgraph(options: number | { limit?: number; mode?: string; nodeId?: string; q?: string } = 100): Promise<GraphResponse> {
    const params = new URLSearchParams();
    if (typeof options === "number") {
      params.set("limit", String(options));
    } else {
      params.set("limit", String(options.limit ?? 100));
      if (options.mode) params.set("mode", options.mode);
      if (options.nodeId) params.set("node_id", options.nodeId);
      if (options.q) params.set("q", options.q);
    }
    return request<GraphResponse>(`/api/v1/graph/subgraph?${params.toString()}`);
  },

  graphSearch(q: string): Promise<GraphResponse> {
    return request<GraphResponse>(`/api/v1/graph/search?q=${encodeURIComponent(q)}`);
  },

  graphNeighbors(nodeId: string, limit = 80): Promise<GraphResponse> {
    return request<GraphResponse>(`/api/v1/graph/neighbors/${encodeURIComponent(nodeId)}?limit=${encodeURIComponent(String(limit))}`);
  },

  streamJob(
    jobId: string,
    onEvent: (event: RuntimeEvent | { event_type: "final"; job_id: string; status: string; message: string }) => void,
    onError: (error: ReguThinkInteractiveError) => void,
  ): () => void {
    const source = new EventSource(`${API_BASE_URL}/api/v1/jobs/${encodeURIComponent(jobId)}/stream`);

    const handleRuntimeEvent = (event: MessageEvent<string>) => {
      try {
        onEvent(JSON.parse(event.data) as RuntimeEvent);
      } catch (error) {
        onError(new ReguThinkInteractiveError("parse", error instanceof Error ? error.message : "SSE parse failure"));
      }
    };

    source.addEventListener("final", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent<string>).data) as {
          job_id?: string;
          status?: string;
          message?: string;
        };
        onEvent({
          event_type: "final",
          job_id: payload.job_id ?? jobId,
          status: payload.status ?? "unknown",
          message: payload.message ?? "Stream closed.",
        });
      } catch {
        onEvent({ event_type: "final", job_id: jobId, status: "unknown", message: "Stream closed." });
      }
      source.close();
    });

    source.onmessage = handleRuntimeEvent;
    [
      "job_created",
      "uploaded_material_intake_started",
      "uploaded_material_intake_completed",
      "uploaded_materials_loaded",
      "material_parsing_started",
      "material_parsing_completed",
      "fact_extraction_started",
      "fact_extraction_completed",
      "case_profile_resolved",
      "dynamic_case_profile_started",
      "dynamic_case_profile_completed",
      "legal_retrieval_started",
      "legal_retrieval_completed",
      "evidence_pack_started",
      "evidence_pack_completed",
      "citation_plan_started",
      "citation_plan_completed",
      "agent_analysis_started",
      "legal_agent_completed",
      "business_agent_completed",
      "technical_agent_completed",
      "risk_agent_completed",
      "auditor_agent_completed",
      "writer_agent_completed",
      "report_generation_started",
      "report_generation_completed",
      "autojudge_started",
      "autojudge_completed",
      "llm_judge_unavailable",
      "quality_gate_started",
      "quality_gate_completed",
      "job_completed",
      "job_failed",
      "placeholder_report_created",
      "runtime_adapter_not_configured",
      "runtime_contract_not_supported",
    ].forEach((eventName) => source.addEventListener(eventName, handleRuntimeEvent));
    source.onerror = () => {
      onError(new ReguThinkInteractiveError("stream", "SSE stream closed or unavailable."));
      source.close();
    };

    return () => source.close();
  },
};
