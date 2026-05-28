"""Tests for MultiAgentRuntimeOrchestrator."""
import pytest
from uuid import uuid4

from app.models.assessment import AssessmentType
from app.models.job import JobStatus, RunAssessmentRequest, RuntimeJob, RuntimeMode
from app.services.runtime_storage import RuntimeStorage


def _make_job(assessment_type: str = "data_transaction_compliance") -> RuntimeJob:
    return RuntimeJob(
        job_id=f"job_{uuid4().hex}",
        conversation_id=f"conv_{uuid4().hex}",
        assessment_type=AssessmentType(assessment_type),
        status=JobStatus.queued,
        user_prompt="数据交易合规评估测试",
        runtime_mode=RuntimeMode.uploaded_material_runtime,
    )


def test_orchestrator_run_data_transaction():
    from app.services.multi_agent_runtime_orchestrator import MultiAgentRuntimeOrchestrator
    from app.services.uploaded_material_intake_service import UploadedMaterialIntakeService

    orchestrator = MultiAgentRuntimeOrchestrator()
    intake_service = UploadedMaterialIntakeService()
    job = _make_job("data_transaction_compliance")

    intake = intake_service.intake([], "数据交易合规评估测试")

    artifacts = orchestrator.run(
        job,
        job.conversation_id,
        "请评估数据交易合规性",
        "data_transaction_compliance",
        [],
        [],
        intake,
    )

    assert isinstance(artifacts, dict)
    assert len(artifacts) >= 10
    assert "extracted_facts.json" in artifacts
    assert "dynamic_case_profile.json" in artifacts
    assert "runtime_route.json" in artifacts
    assert "risk_score.json" in artifacts
    assert "prototype_report.md" in artifacts
    assert "boundary_audit.json" in artifacts


def test_orchestrator_run_cross_border():
    from app.services.multi_agent_runtime_orchestrator import MultiAgentRuntimeOrchestrator
    from app.services.uploaded_material_intake_service import UploadedMaterialIntakeService

    orchestrator = MultiAgentRuntimeOrchestrator()
    intake_service = UploadedMaterialIntakeService()
    job = _make_job("cross_border_data_transfer")

    intake = intake_service.intake([], "数据需要出境到境外接收方")

    artifacts = orchestrator.run(
        job,
        job.conversation_id,
        "数据需要出境到境外接收方",
        "cross_border_data_transfer",
        [],
        [],
        intake,
    )

    assert "prototype_report.md" in artifacts
    assert "risk_score.json" in artifacts


def test_orchestrator_generates_all_required_artifacts():
    from app.services.multi_agent_runtime_orchestrator import MultiAgentRuntimeOrchestrator
    from app.services.uploaded_material_intake_service import UploadedMaterialIntakeService

    orchestrator = MultiAgentRuntimeOrchestrator()
    intake_service = UploadedMaterialIntakeService()
    job = _make_job()

    intake = intake_service.intake([], "测试")

    artifacts = orchestrator.run(job, job.conversation_id, "测试", "data_transaction_compliance", [], [], intake)

    required = [
        "extracted_facts.json", "dynamic_case_profile.json", "runtime_route.json",
        "retrieval_trace.json", "claim_plan.json", "evidence_pack.json",
        "citation_plan.json", "compliance_analysis.json", "risk_score.json",
        "source_trace.json", "runtime_manifest.json", "boundary_audit.json",
        "missing_capabilities.json", "prototype_report.md",
    ]
    for name in required:
        assert name in artifacts, f"Missing artifact: {name}"


def test_orchestrator_does_not_write_chroma():
    from app.services.multi_agent_runtime_orchestrator import MultiAgentRuntimeOrchestrator
    from app.services.uploaded_material_intake_service import UploadedMaterialIntakeService

    orchestrator = MultiAgentRuntimeOrchestrator()
    intake_service = UploadedMaterialIntakeService()
    job = _make_job()
    intake = intake_service.intake([], "测试")

    artifacts = orchestrator.run(job, job.conversation_id, "测试", "data_transaction_compliance", [], [], intake)

    storage = RuntimeStorage()
    boundary_path = storage.artifacts_dir(job.job_id) / "boundary_audit.json"
    assert boundary_path.exists()
    import json
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    assert boundary["uploaded_files_written_to_chroma"] is False
    assert boundary["uploaded_files_written_to_neo4j"] is False


def test_orchestrator_not_formal_legal_opinion():
    from app.services.multi_agent_runtime_orchestrator import MultiAgentRuntimeOrchestrator
    from app.services.uploaded_material_intake_service import UploadedMaterialIntakeService

    orchestrator = MultiAgentRuntimeOrchestrator()
    intake_service = UploadedMaterialIntakeService()
    job = _make_job()
    intake = intake_service.intake([], "测试")

    artifacts = orchestrator.run(job, job.conversation_id, "测试", "data_transaction_compliance", [], [], intake)

    storage = RuntimeStorage()
    report_path = storage.artifacts_dir(job.job_id) / "prototype_report.md"
    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "非正式法律意见" in report
    assert "prototype" in report.lower()
    assert "not_formal_legal_opinion" in report.lower() or "非正式" in report