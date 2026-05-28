from fastapi.testclient import TestClient

from app.api.v1.router import api_router
from app.main import app
from app.models.chat import CreateConversationRequest
from app.services.llm_chat_service import LLMChatService

client = TestClient(app)


def _mock_llm(monkeypatch):
    def complete(self, *, user_message, intent, rag_context=None, uploaded_context=None):
        return {
            "llm_used": True,
            "llm_unavailable": False,
            "content": f"测试助手回复：{user_message}",
            "llm_config": {"test_mock": True},
        }

    monkeypatch.setattr(LLMChatService, "complete", complete)


def _create_conversation():
    resp = client.post(
        "/api/v1/conversations",
        json={"title": "API test", "assessment_type": "data_transaction_compliance"},
    )
    assert resp.status_code == 200
    return resp.json()["conversation_id"]


def test_chat_endpoint_creates_messages(monkeypatch):
    _mock_llm(monkeypatch)
    conv_id = _create_conversation()
    resp = client.post(
        f"/api/v1/conversations/{conv_id}/chat",
        json={"content": "请做数据交易合规评估。", "assessment_type": "data_transaction_compliance", "rag_enabled": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_message"]["role"] == "user"
    assert data["assistant_message"]["role"] == "assistant"
    assert len(data["assistant_message"]["content"]) > 0
    assert data["job_id"] is None


def test_chat_endpoint_auto_run_without_files_is_blocked():
    conv_id = _create_conversation()
    resp = client.post(
        f"/api/v1/conversations/{conv_id}/chat",
        json={
            "content": "请评估数据合规性。",
            "assessment_type": "data_transaction_compliance",
            "auto_run_assessment": True,
            "runtime_mode": "dry_run",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] is None
    assert data["full_chain_job_created"] is False
    assert data["chat_metadata"]["chat_mode"] == "report_request_blocked"


def test_chat_endpoint_no_files_replies(monkeypatch):
    _mock_llm(monkeypatch)
    conv_id = _create_conversation()
    resp = client.post(
        f"/api/v1/conversations/{conv_id}/chat",
        json={"content": "评估数据合规性。", "file_ids": [], "rag_enabled": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["uploaded_material_intake"]["file_count"] == 0
    assert data["assistant_message"]["role"] == "assistant"


def test_chat_endpoint_unknown_conversation_returns_404():
    resp = client.post(
        "/api/v1/conversations/conv_nonexistent/chat",
        json={"content": "test"},
    )
    assert resp.status_code == 404


def test_chat_endpoint_boundary_flags_present(monkeypatch):
    _mock_llm(monkeypatch)
    conv_id = _create_conversation()
    resp = client.post(
        f"/api/v1/conversations/{conv_id}/chat",
        json={"content": "测试", "rag_enabled": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["boundary_flags"]["not_production_ready"] is True
    assert data["boundary_flags"]["not_source_backed_pass"] is True


def test_chat_endpoint_intent_present(monkeypatch):
    _mock_llm(monkeypatch)
    conv_id = _create_conversation()
    resp = client.post(
        f"/api/v1/conversations/{conv_id}/chat",
        json={"content": "跨境数据传输需要做安全评估。", "rag_enabled": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"]["detected_type"] == "cross_border_data_transfer"
