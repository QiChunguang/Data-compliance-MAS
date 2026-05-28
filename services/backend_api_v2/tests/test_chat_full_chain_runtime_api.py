"""Test /chat API with full_chain_runtime mode."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.assessment import AssessmentType
from app.models.job import RuntimeMode


client = TestClient(app)


def _upload_text_file(conversation_id: str, name: str = "material.txt") -> str:
    resp = client.post(
        f"/api/v1/conversations/{conversation_id}/files",
        files={"file": (name, "甲方与乙方拟开展数据交易，涉及个人信息、交易记录和安全控制措施。", "text/plain")},
    )
    assert resp.status_code == 200
    return resp.json()["file_id"]


@pytest.fixture
def conversation():
    resp = client.post("/api/v1/conversations", json={
        "title": "Full Chain Test",
        "assessment_type": "data_transaction_compliance",
    })
    assert resp.status_code == 200
    data = resp.json()
    return data["conversation_id"]


class TestChatFullChainRuntimeAPI:

    def test_chat_full_chain_runtime_creates_job(self, conversation):
        file_id = _upload_text_file(conversation)
        resp = client.post(f"/api/v1/conversations/{conversation}/chat", json={
            "content": "请运行完整多智能体数据交易合规评估，并给出报告和AutoJudge评分。",
            "assessment_type": "data_transaction_compliance",
            "file_ids": [file_id],
            "auto_run_assessment": True,
            "runtime_mode": "full_chain_runtime",
            "action": "run_full_chain_report",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["job_id"] is not None
        assert data["runtime_mode_effective"] == "full_chain_runtime"
        assert data["auto_judge_expected"] is True
        assert data["full_chain_runtime_supported"] is True
        assert data["report_generated"] is False

    def test_chat_full_chain_without_files_blocks(self, conversation):
        resp = client.post(f"/api/v1/conversations/{conversation}/chat", json={
            "content": "评估数据交易合规性",
            "assessment_type": "data_transaction_compliance",
            "file_ids": [],
            "auto_run_assessment": True,
            "runtime_mode": "full_chain_runtime",
            "action": "run_full_chain_report",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] is None
        assert data["full_chain_job_created"] is False

    def test_chat_full_chain_cross_border(self, conversation):
        file_id = _upload_text_file(conversation, "cross-border.txt")
        resp = client.post(f"/api/v1/conversations/{conversation}/chat", json={
            "content": "我有一批财务数据需要出境，请运行跨境数据传输合规评估",
            "assessment_type": "cross_border_data_transfer",
            "file_ids": [file_id],
            "auto_run_assessment": True,
            "runtime_mode": "full_chain_runtime",
            "action": "run_full_chain_report",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] is not None

    def test_chat_send_message_still_works(self, conversation):
        resp = client.post(f"/api/v1/conversations/{conversation}/chat", json={
            "content": "你好",
            "assessment_type": "general_data_compliance_diagnostic",
            "file_ids": [],
            "auto_run_assessment": False,
            "runtime_mode": "chat",
            "action": "send_message",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["runtime_mode_effective"] == "chat"
        assert data["auto_judge_expected"] is False
        assert data["job_id"] is None

    def test_async_job_status_accessible(self, conversation):
        file_id = _upload_text_file(conversation)
        resp = client.post(f"/api/v1/conversations/{conversation}/chat", json={
            "content": "数据交易合规评估",
            "assessment_type": "data_transaction_compliance",
            "file_ids": [file_id],
            "auto_run_assessment": True,
            "runtime_mode": "full_chain_runtime",
            "action": "run_full_chain_report",
        })
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]

        job_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert job_resp.status_code == 200
        assert job_resp.json()["status"] in {"queued", "running", "completed", "failed"}

    def test_job_events_accessible(self, conversation):
        file_id = _upload_text_file(conversation)
        resp = client.post(f"/api/v1/conversations/{conversation}/chat", json={
            "content": "数据交易合规评估",
            "assessment_type": "data_transaction_compliance",
            "file_ids": [file_id],
            "auto_run_assessment": True,
            "runtime_mode": "full_chain_runtime",
            "action": "run_full_chain_report",
        })
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]

        events_resp = client.get(f"/api/v1/jobs/{job_id}/events")
        assert events_resp.status_code == 200

    def test_cross_border_intent_detection_in_chat(self, conversation):
        resp = client.post(f"/api/v1/conversations/{conversation}/chat", json={
            "content": "我需要将数据传输到海外",
            "assessment_type": "general_data_compliance_diagnostic",
            "file_ids": [],
            "auto_run_assessment": False,
            "runtime_mode": "dry_run",
        })
        assert resp.status_code == 200
        data = resp.json()
        intent = data.get("intent", {})
        assert isinstance(intent, dict)
