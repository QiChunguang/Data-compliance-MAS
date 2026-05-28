from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app
from app.models.chat import CreateConversationRequest, CreateMessageRequest
from app.models.job import JobStatus, RuntimeJob, RuntimeMode
from app.services.audit_evidence_renderer import AuditEvidenceRenderer, sanitize_evidence_text
from app.services.conversation_service import ConversationService
from app.services.runtime_job_service import RuntimeJobService
from app.services.user_report_render_service import UserReportRenderService

client = TestClient(app)


def test_user_report_has_business_sections_and_no_debug_terms():
    report = UserReportRenderService().render(
        assessment_type="data_transaction_compliance",
        user_prompt="请审查数据交易材料",
        facts={"parties": ["甲方", "乙方"], "missing_facts": ["授权证明"]},
        claims=[{"title": "数据来源合法性", "check": "需核验授权链条"}],
        citations=[{"law_reference": "个人信息保护法", "content": "处理个人信息应有合法基础"}],
        risk_score={"overall_risk_level": "medium"},
        evidence_pack={"evidence_items": [{"source_title": "个人信息保护法", "content": "合法基础"}]},
        retrieval_trace=None,
        file_records=[],
    )
    for section in [
        "审查对象与材料范围",
        "业务事实摘要",
        "适用法律依据",
        "核心合规风险",
        "证据与引用",
        "整改建议",
        "证据边界与人工复核状态",
        "免责声明",
    ]:
        assert f"## {section}" in report
    for forbidden in ["AutoJudge", "prototype", "dry-run", "full-chain", "support_level", "needs_manual_verification"]:
        assert forbidden not in report


def test_conversation_memory_five_files_created(tmp_path: Path):
    service = ConversationService()
    service.storage.root = tmp_path / "runtime_storage"
    service.memory.storage.root = service.storage.root
    conv = service.create_conversation(CreateConversationRequest(title="BE8.3 memory"))
    service.add_message(conv.conversation_id, CreateMessageRequest(content="hello", attachments=[]))
    memory_dir = service.storage.conversation_memory_dir(conv.conversation_id)
    expected = [
        "messages.jsonl",
        "memory_summary.md",
        "memory_summary.json",
        "uploaded_files_index.json",
        "latest_context_pack.json",
    ]
    for name in expected:
        assert (memory_dir / name).exists()
    summary = (memory_dir / "memory_summary.md").read_text(encoding="utf-8")
    assert "no secrets" in summary


def test_artifact_download_guards(tmp_path):
    from app.api.v1.endpoints import jobs as jobs_endpoint

    job_service = jobs_endpoint.job_service
    old_root = job_service.storage.root
    job_service.storage.root = tmp_path / "runtime_storage"
    job = RuntimeJob(
        job_id="job_be83_download_guard",
        conversation_id="conv_be83_download_guard",
        assessment_type="data_transaction_compliance",
        status=JobStatus.completed,
        runtime_mode=RuntimeMode.full_chain_runtime,
        user_prompt="download",
    )
    try:
        job_service._save_job(job)
        artifact_dir = job_service.storage.artifacts_dir(job.job_id)
        (artifact_dir / "user_report.md").write_text("# ok\n", encoding="utf-8")

        ok = client.get(f"/api/v1/jobs/{job.job_id}/artifacts/user_report.md/download")
        assert ok.status_code == 200
        missing = client.get(f"/api/v1/jobs/{job.job_id}/artifacts/missing.md/download")
        assert missing.status_code == 404
        traversal = client.get(f"/api/v1/jobs/{job.job_id}/artifacts/..%2Fjob.json/download")
        assert traversal.status_code in {400, 404}
    finally:
        job_service.storage.root = old_root


def test_audit_renderer_rejects_object_pollution(tmp_path: Path):
    renderer = AuditEvidenceRenderer()
    status = {
        "phase": "Phase12-BE8.3-FE8.3",
        "overall_status": "passed",
        "backend_functional_status": "passed",
        "frontend_product_status": "passed",
        "report_quality_status": "passed",
        "graph_ux_status": "passed",
        "audit_evidence_status": "passed",
        "evidence": {"screenshots_count": 12},
    }
    md = renderer.render_markdown(status, title="BE8.3 Audit")
    assert sanitize_evidence_text(md) == []
    assert "$(@{" not in md
    bad = dict(status)
    bad["warnings"] = ["System.Object[]"]
    try:
        renderer.render_markdown(bad, title="Bad Audit")
        assert False, "renderer should reject object dumps"
    except ValueError:
        pass
