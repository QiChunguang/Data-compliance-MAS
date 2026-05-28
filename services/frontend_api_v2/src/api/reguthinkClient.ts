import type {
  BaselineStatusResponse,
  CaseArtifactsResponse,
  CaseDetailResponse,
  CaseListResponse,
  HealthResponse,
  ReportResponse,
  RuntimeRunCaseResponse,
} from "../types/reguthink-api";
import { REGUTHINK_API_BASE_URL } from "./reguthinkConfig";

export const API_BASE_URL = REGUTHINK_API_BASE_URL;

export type ReguThinkClientErrorKind =
  | "network"
  | "not_found"
  | "server"
  | "http"
  | "json_parse";

export class ReguThinkClientError extends Error {
  readonly kind: ReguThinkClientErrorKind;
  readonly status?: number;
  readonly endpoint: string;

  constructor(kind: ReguThinkClientErrorKind, endpoint: string, message: string, status?: number) {
    super(message);
    this.name = "ReguThinkClientError";
    this.kind = kind;
    this.status = status;
    this.endpoint = endpoint;
  }
}

async function requestJson<T>(endpoint: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  let response: Response;

  try {
    response = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch (error) {
    if (globalThis.location?.origin) {
      try {
        response = await fetch(endpoint, {
          ...init,
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            ...init?.headers,
          },
        });
      } catch (proxyError) {
        const detail = proxyError instanceof Error ? proxyError.message : "unknown network error";
        throw new ReguThinkClientError(
          "network",
          endpoint,
          `Backend down or network error while calling ${endpoint}: ${detail}`,
        );
      }
    } else {
      const detail = error instanceof Error ? error.message : "unknown network error";
      throw new ReguThinkClientError(
        "network",
        endpoint,
        `Backend down or network error while calling ${endpoint}: ${detail}`,
      );
    }
  }

  if (!response.ok) {
    const message = `HTTP ${response.status} while calling ${endpoint}`;
    if (response.status === 404) {
      throw new ReguThinkClientError("not_found", endpoint, message, response.status);
    }
    if (response.status >= 500) {
      throw new ReguThinkClientError("server", endpoint, message, response.status);
    }
    throw new ReguThinkClientError("http", endpoint, message, response.status);
  }

  try {
    return (await response.json()) as T;
  } catch (error) {
    const detail = error instanceof Error ? error.message : "unknown network error";
    throw new ReguThinkClientError(
      "json_parse",
      endpoint,
      `JSON parse failure while calling ${endpoint}: ${detail}`,
      response.status,
    );
  }
}

export const reguthinkClient = {
  getHealth: () => requestJson<HealthResponse>("/api/v1/health"),
  getBaselineStatus: () => requestJson<BaselineStatusResponse>("/api/v1/baseline/status"),
  getCases: () => requestJson<CaseListResponse>("/api/v1/cases"),
  getCase: (caseId: string) =>
    requestJson<CaseDetailResponse>(`/api/v1/cases/${encodeURIComponent(caseId)}`),
  getCaseArtifacts: (caseId: string) =>
    requestJson<CaseArtifactsResponse>(`/api/v1/cases/${encodeURIComponent(caseId)}/artifacts`),
  getCaseReport: (caseId: string) =>
    requestJson<ReportResponse>(`/api/v1/cases/${encodeURIComponent(caseId)}/report`),
  runCaseDryRun: (caseId: string) =>
    requestJson<RuntimeRunCaseResponse>("/api/v1/runtime/run-case", {
      method: "POST",
      body: JSON.stringify({ case_id: caseId, dry_run: true }),
    }),
};
