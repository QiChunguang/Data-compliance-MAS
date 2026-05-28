# ReguThink Interactive API Contract v1

Phase: Phase12-BE2-InteractiveChatFileUploadRuntimeBackend

## Boundary

Interactive APIs are prototype diagnostic APIs. They MUST NOT present output as formal legal advice and MUST NOT fabricate `source_backed`, `manual_verified`, or `article_level_verified`.

Uploaded files are stored only under `services/backend_api_v2/runtime_storage` and are not written to Chroma, Neo4j, `legal_data`, or `current_backend.json`.

## Endpoints

- `POST /api/v1/conversations`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{conversation_id}`
- `GET /api/v1/conversations/{conversation_id}/messages`
- `POST /api/v1/conversations/{conversation_id}/messages`
- `POST /api/v1/conversations/{conversation_id}/files`
- `GET /api/v1/conversations/{conversation_id}/files`
- `GET /api/v1/files/{file_id}`
- `GET /api/v1/assessment-types`
- `POST /api/v1/conversations/{conversation_id}/assessments/run`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/events`
- `GET /api/v1/jobs/{job_id}/artifacts`
- `POST /api/v1/jobs/{job_id}/cancel`
- `GET /api/v1/jobs/{job_id}/stream`

## Runtime Modes

`dry_run` creates persisted events and placeholder artifacts without real multi-agent execution.

`controlled_runtime` is blocked unless explicitly enabled and configured. In BE2 it returns `runtime_adapter_not_configured` rather than guessing a core/v12 invocation.

## File Upload

Allowed extensions: `.txt`, `.md`, `.json`, `.csv`, `.pdf`, `.docx`, `.xlsx`.

The API rejects empty files, disallowed extensions, oversize files, and unsafe filenames. API responses expose relative `stored_path` / `display_path` only.

## SSE

`GET /api/v1/jobs/{job_id}/stream` returns `text/event-stream`, emits job events, sends a `final` event for terminal statuses, then closes the connection.
