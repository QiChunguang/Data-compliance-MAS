from app.models.assessment import AssessmentType
from app.models.chat import CreateConversationRequest
from app.models.job import JobStatus, RunAssessmentRequest, RuntimeMode
from app.core.config import get_settings
from app.services.conversation_service import ConversationService
from app.services.runtime_event_service import RuntimeEventService
from app.services.runtime_job_service import RuntimeJobService
from app.services.runtime_storage import RuntimeStorage


def test_dry_run_job_writes_events_and_artifacts():
    conversation = ConversationService().create_conversation(CreateConversationRequest(title="job test"))
    job = RuntimeJobService().create_and_run(
        conversation.conversation_id,
        RunAssessmentRequest(
            assessment_type=AssessmentType.general_data_compliance_diagnostic,
            user_prompt="diagnose this material",
            runtime_mode=RuntimeMode.dry_run,
        ),
    )
    assert job.status == JobStatus.completed
    storage = RuntimeStorage()
    assert storage.job_json(job.job_id).exists()
    assert storage.events_jsonl(job.job_id).exists()
    assert (storage.artifacts_dir(job.job_id) / "runtime_result.json").exists()
    events = RuntimeEventService().list_events(job.job_id)
    assert events[-1].event_type == "final"


def test_controlled_runtime_disabled_fails_safely(monkeypatch):
    monkeypatch.setenv("REGUTHINK_API_ENABLE_RUNTIME", "0")
    monkeypatch.setenv("REGUTHINK_API_RUNTIME_MODE", "disabled")
    get_settings.cache_clear()
    conversation = ConversationService().create_conversation(CreateConversationRequest(title="runtime disabled"))
    job = RuntimeJobService().create_and_run(
        conversation.conversation_id,
        RunAssessmentRequest(
            assessment_type=AssessmentType.general_data_compliance_diagnostic,
            user_prompt="try real runtime",
            runtime_mode=RuntimeMode.controlled_runtime,
        ),
    )
    assert job.status == JobStatus.failed
    assert job.error_message == "runtime_adapter_not_configured"
    assert job.boundary_flags["local_neural_reranker_default_enabled"] is False
    get_settings.cache_clear()
