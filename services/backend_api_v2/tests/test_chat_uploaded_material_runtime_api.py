"""Tests for chat endpoint with uploaded_material_runtime mode."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_chat_dry_run_creates_no_job(client):
    conv_resp = client.post("/api/v1/conversations", json={
        "title": "dry test",
        "assessment_type": "data_transaction_compliance",
    })
    assert conv_resp.status_code == 200
    conv_id = conv_resp.json()["conversation_id"]

    chat_resp = client.post(f"/api/v1/conversations/{conv_id}/chat", json={
        "content": "测试消息",
        "assessment_type": "data_transaction_compliance",
        "file_ids": [],
        "auto_run_assessment": False,
        "runtime_mode": "dry_run",
    })
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["user_message"]["role"] == "user"
    assert data["assistant_message"]["role"] == "assistant"
    assert data["job_id"] is None


def test_chat_uploaded_material_runtime_without_files_blocks_job(client):
    conv_resp = client.post("/api/v1/conversations", json={
        "title": "uploaded runtime test",
        "assessment_type": "data_transaction_compliance",
    })
    assert conv_resp.status_code == 200
    conv_id = conv_resp.json()["conversation_id"]

    chat_resp = client.post(f"/api/v1/conversations/{conv_id}/chat", json={
        "content": "请基于材料执行数据交易合规评估",
        "assessment_type": "data_transaction_compliance",
        "file_ids": [],
        "auto_run_assessment": True,
        "runtime_mode": "uploaded_material_runtime",
    })
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["job_id"] is None
    assert data["full_chain_job_created"] is False
    assert data["chat_metadata"]["chat_mode"] == "report_request_blocked"


def test_chat_uploaded_material_runtime_generates_extracted_facts(client):
    conv_resp = client.post("/api/v1/conversations", json={
        "title": "facts test",
        "assessment_type": "data_transaction_compliance",
    })
    conv_id = conv_resp.json()["conversation_id"]

    chat_resp = client.post(f"/api/v1/conversations/{conv_id}/chat", json={
        "content": "甲方和乙方进行个人信息数据交易",
        "assessment_type": "data_transaction_compliance",
        "file_ids": [],
        "auto_run_assessment": True,
        "runtime_mode": "uploaded_material_runtime",
    })
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["job_id"] is None
    assert data["full_chain_job_created"] is False


def test_chat_uploaded_material_runtime_sse_events(client):
    conv_resp = client.post("/api/v1/conversations", json={
        "title": "sse test",
        "assessment_type": "cross_border_data_transfer",
    })
    conv_id = conv_resp.json()["conversation_id"]

    chat_resp = client.post(f"/api/v1/conversations/{conv_id}/chat", json={
        "content": "数据需要出境到境外",
        "assessment_type": "cross_border_data_transfer",
        "file_ids": [],
        "auto_run_assessment": True,
        "runtime_mode": "uploaded_material_runtime",
    })
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["job_id"] is None
    assert data["chat_metadata"]["chat_mode"] == "report_request_blocked"


def test_chat_boundary_audit_no_fabrication(client):
    conv_resp = client.post("/api/v1/conversations", json={
        "title": "boundary test",
        "assessment_type": "data_transaction_compliance",
    })
    conv_id = conv_resp.json()["conversation_id"]

    chat_resp = client.post(f"/api/v1/conversations/{conv_id}/chat", json={
        "content": "测试",
        "assessment_type": "data_transaction_compliance",
        "file_ids": [],
        "auto_run_assessment": True,
        "runtime_mode": "uploaded_material_runtime",
    })
    data = chat_resp.json()
    assert data["boundary_flags"]["not_production_ready"] is True
    assert data["full_chain_job_created"] is False
