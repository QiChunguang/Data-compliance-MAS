from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_controlled_runtime_disabled_fails_safely(monkeypatch):
    monkeypatch.setenv("REGUTHINK_API_ENABLE_RUNTIME", "0")
    monkeypatch.setenv("REGUTHINK_API_RUNTIME_MODE", "disabled")
    get_settings.cache_clear()
    client = TestClient(app)
    conversation = client.post(
        "/api/v1/conversations",
        json={"title": "disabled runtime", "assessment_type": "general_data_compliance_diagnostic"},
    ).json()
    response = client.post(
        f"/api/v1/conversations/{conversation['conversation_id']}/assessments/run",
        json={
            "assessment_type": "general_data_compliance_diagnostic",
            "user_prompt": "case_id=ai_training_dataset_trade",
            "file_ids": [],
            "runtime_mode": "controlled_runtime",
        },
    )
    assert response.status_code == 200
    job = client.get(f"/api/v1/jobs/{response.json()['job_id']}").json()
    assert job["status"] == "failed"
    assert job["error_message"] == "runtime_adapter_not_configured"


def test_controlled_case_runtime_smoke(monkeypatch):
    monkeypatch.setenv("REGUTHINK_PROJECT_ROOT", "D:\\Python\\Pycharm\\Agent_data")
    monkeypatch.setenv("REGUTHINK_API_ENABLE_RUNTIME", "1")
    monkeypatch.setenv("REGUTHINK_API_RUNTIME_MODE", "controlled")
    monkeypatch.setenv("REGUTHINK_API_ENABLE_REAL_AUTOJUDGE", "0")
    monkeypatch.setenv("REGUTHINK_API_ALLOW_UPLOADED_MATERIAL_RUNTIME", "0")
    get_settings.cache_clear()
    client = TestClient(app)
    health = client.get("/api/v1/health").json()
    assert health["controlled_case_runtime_supported"] is True
    assert health["uploaded_material_runtime_supported"] is True
    assert health["full_chain_runtime_supported"] is True
    assert health["local_neural_reranker_default_enabled"] is False

    conversation = client.post(
        "/api/v1/conversations",
        json={"title": "controlled smoke", "assessment_type": "general_data_compliance_diagnostic"},
    ).json()
    response = client.post(
        f"/api/v1/conversations/{conversation['conversation_id']}/assessments/run",
        json={
            "assessment_type": "general_data_compliance_diagnostic",
            "user_prompt": "case_id=ai_training_dataset_trade",
            "file_ids": [],
            "runtime_mode": "controlled_runtime",
        },
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    job = client.get(f"/api/v1/jobs/{job_id}").json()
    assert job["status"] == "completed"
    artifacts = client.get(f"/api/v1/jobs/{job_id}/artifacts").json()["artifacts"]
    assert "runtime_manifest.json" in artifacts
    assert "report.md" in artifacts
    assert "missing_artifacts.json" in artifacts
    events = client.get(f"/api/v1/jobs/{job_id}/events").json()["events"]
    assert events[-1]["event_type"] == "final"

    get_settings.cache_clear()
