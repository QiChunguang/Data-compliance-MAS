from app.models.chat import CreateConversationRequest
from app.models.job import RuntimeMode
from app.services.chat_orchestrator_service import ChatOrchestratorService, ChatRequest
from app.services.conversation_service import ConversationService
from app.services.llm_chat_service import LLMChatService


def _mock_llm(monkeypatch):
    def complete(self, *, user_message, intent, rag_context=None, uploaded_context=None):
        return {
            "llm_used": True,
            "llm_unavailable": False,
            "content": f"测试助手回复：{user_message}",
            "llm_config": {"test_mock": True},
        }

    monkeypatch.setattr(LLMChatService, "complete", complete)


def test_chat_creates_user_and_assistant_messages(monkeypatch):
    _mock_llm(monkeypatch)
    service = ChatOrchestratorService()
    conversations = ConversationService()
    conv = conversations.create_conversation(CreateConversationRequest(title="chat test"))
    resp = service.chat(conv.conversation_id, ChatRequest(content="请做数据交易合规评估。", rag_enabled=False))
    assert resp.user_message["role"] == "user"
    assert resp.assistant_message["role"] == "assistant"
    assert len(resp.assistant_message["content"]) > 0
    assert resp.job_id is None


def test_chat_no_files_still_replies(monkeypatch):
    _mock_llm(monkeypatch)
    service = ChatOrchestratorService()
    conversations = ConversationService()
    conv = conversations.create_conversation(CreateConversationRequest(title="no files test"))
    resp = service.chat(conv.conversation_id, ChatRequest(content="评估数据处理合规性。", rag_enabled=False))
    assert resp.uploaded_material_intake["file_count"] == 0
    assert resp.assistant_message["role"] == "assistant"


def test_chat_detects_intent(monkeypatch):
    _mock_llm(monkeypatch)
    service = ChatOrchestratorService()
    conversations = ConversationService()
    conv = conversations.create_conversation(CreateConversationRequest(title="intent test"))
    resp = service.chat(conv.conversation_id, ChatRequest(content="跨境数据传输需要满足什么合规要求？", rag_enabled=False))
    assert resp.intent["detected_type"] == "cross_border_data_transfer"


def test_auto_run_assessment_false_no_job(monkeypatch):
    _mock_llm(monkeypatch)
    service = ChatOrchestratorService()
    conversations = ConversationService()
    conv = conversations.create_conversation(CreateConversationRequest(title="no auto run"))
    resp = service.chat(conv.conversation_id, ChatRequest(content="评估", auto_run_assessment=False, rag_enabled=False))
    assert resp.job_id is None


def test_auto_run_assessment_true_without_files_blocks_job():
    service = ChatOrchestratorService()
    conversations = ConversationService()
    conv = conversations.create_conversation(CreateConversationRequest(title="auto run test"))
    resp = service.chat(conv.conversation_id, ChatRequest(
        content="请评估数据交易合规性。",
        auto_run_assessment=True,
        runtime_mode=RuntimeMode.dry_run,
    ))
    assert resp.job_id is None
    assert resp.full_chain_job_created is False
    assert resp.chat_metadata["chat_mode"] == "report_request_blocked"


def test_chat_boundary_flags_present(monkeypatch):
    _mock_llm(monkeypatch)
    service = ChatOrchestratorService()
    conversations = ConversationService()
    conv = conversations.create_conversation(CreateConversationRequest(title="boundary test"))
    resp = service.chat(conv.conversation_id, ChatRequest(content="测试", rag_enabled=False))
    assert resp.boundary_flags["not_production_ready"] is True
    assert resp.boundary_flags["not_source_backed_pass"] is True
    assert resp.boundary_flags["not_human_reviewed"] is True


def test_chat_suggested_next_actions(monkeypatch):
    _mock_llm(monkeypatch)
    service = ChatOrchestratorService()
    conversations = ConversationService()
    conv = conversations.create_conversation(CreateConversationRequest(title="actions test"))
    resp = service.chat(conv.conversation_id, ChatRequest(content="请做合规评估。", rag_enabled=False))
    assert len(resp.suggested_next_actions) > 0
    assert any("run_full_chain_report" in action for action in resp.suggested_next_actions)
