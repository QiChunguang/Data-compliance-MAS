from pathlib import Path

from fastapi.testclient import TestClient

from app.core.boundaries import BOUNDARY_FLAGS
from app.core.project_paths import get_project_paths
from app.main import app


client = TestClient(app)


def test_health_interactive_flags():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["runtime_enabled"] is False
    assert data["dry_run_assessment_available"] is True
    assert data["controlled_runtime_available"] is False
    assert data["real_multi_agent_runtime_enabled"] is False
    assert data["real_multi_agent_runtime_adapter_status"] == "not_configured_or_disabled"
    assert data["local_neural_reranker_default_enabled"] is False


def test_contract_flow_upload_run_events_stream():
    current_backend = get_project_paths().current_backend_json
    before = current_backend.read_text(encoding="utf-8", errors="replace") if current_backend.exists() else None

    conv = client.post("/api/v1/conversations", json={"title": "contract flow"}).json()
    conversation_id = conv["conversation_id"]

    msg = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "hello", "attachments": []},
    )
    assert msg.status_code == 200

    upload = client.post(
        f"/api/v1/conversations/{conversation_id}/files",
        files={"file": ("中文 文件名.md", b"# hello", "text/markdown")},
    )
    assert upload.status_code == 200
    uploaded = upload.json()
    assert uploaded["sha256"]
    assert uploaded["stored_path"].startswith("uploads/")
    assert not Path(uploaded["stored_path"]).is_absolute()

    assessment_types = client.get("/api/v1/assessment-types")
    assert assessment_types.status_code == 200
    assert len(assessment_types.json()["assessment_types"]) == 5

    run = client.post(
        f"/api/v1/conversations/{conversation_id}/assessments/run",
        json={
            "assessment_type": "general_data_compliance_diagnostic",
            "user_prompt": "please assess",
            "file_ids": [uploaded["file_id"]],
            "runtime_mode": "dry_run",
        },
    )
    assert run.status_code == 200
    job_id = run.json()["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}")
    assert job.status_code == 200
    assert job.json()["status"] in {"completed", "running"}

    events = client.get(f"/api/v1/jobs/{job_id}/events")
    assert events.status_code == 200
    assert any(item["event_type"] == "final" for item in events.json()["events"])

    stream = client.get(f"/api/v1/jobs/{job_id}/stream")
    assert stream.status_code == 200
    assert "text/event-stream" in stream.headers["content-type"]
    assert "event: final" in stream.text

    after = current_backend.read_text(encoding="utf-8", errors="replace") if current_backend.exists() else None
    assert before == after
    assert BOUNDARY_FLAGS["local_neural_reranker_default_enabled"] is False
