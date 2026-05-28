"""Test FullChainRuntimeOrchestrator - real multi-agent pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch

from app.models.assessment import AssessmentType
from app.models.job import JobStatus, RuntimeJob, RuntimeMode
from app.services.full_chain_runtime_orchestrator import FullChainRuntimeOrchestrator


@pytest.fixture
def orchestrator():
    return FullChainRuntimeOrchestrator()


@pytest.fixture
def mock_job():
    return RuntimeJob(
        job_id="job_test_full_chain_001",
        conversation_id="conv_test_001",
        assessment_type=AssessmentType.data_transaction_compliance,
        status=JobStatus.running,
        runtime_mode=RuntimeMode.full_chain_runtime,
        user_prompt="请基于上传材料运行完整多智能体数据交易合规评估",
        input_files=[],
    )


@pytest.fixture
def mock_intake():
    from app.services.uploaded_material_intake_service import UploadedMaterialIntake
    return UploadedMaterialIntake()


class TestFullChainRuntimeOrchestrator:

    def test_orchestrator_initializes(self, orchestrator):
        assert orchestrator.bridge is not None
        assert orchestrator.legal_retrieval is not None
        assert orchestrator.claim_service is not None
        assert orchestrator.evidence_service is not None
        assert orchestrator.citation_service is not None
        assert orchestrator.report_service is not None
        assert orchestrator.autojudge_service is not None
        assert orchestrator.quality_gate is not None

    def test_run_generates_core_artifacts(self, orchestrator, mock_job, mock_intake):
        artifacts = orchestrator.run(
            mock_job, "conv_test_001",
            "请运行数据交易合规评估",
            "data_transaction_compliance",
            [], [], mock_intake,
        )

        assert isinstance(artifacts, dict)
        assert "extracted_facts.json" in artifacts
        assert "dynamic_case_profile.json" in artifacts
        assert "runtime_route.json" in artifacts
        assert "claim_plan.json" in artifacts
        assert "retrieval_trace.json" in artifacts
        assert "evidence_pack.json" in artifacts
        assert "citation_plan.json" in artifacts
        assert "risk_score.json" in artifacts
        assert "prototype_report.md" in artifacts

    def test_run_generates_autojudge_artifacts(self, orchestrator, mock_job, mock_intake):
        artifacts = orchestrator.run(
            mock_job, "conv_test_001",
            "请运行数据交易合规评估并给出AutoJudge评分",
            "data_transaction_compliance",
            [], [], mock_intake,
        )

        assert "autojudge_result.json" in artifacts
        assert "score_breakdown.json" in artifacts
        assert "judge_trace.json" in artifacts
        assert "cap_result.json" in artifacts

    def test_run_generates_quality_gate(self, orchestrator, mock_job, mock_intake):
        artifacts = orchestrator.run(
            mock_job, "conv_test_001",
            "请运行评估",
            "data_transaction_compliance",
            [], [], mock_intake,
        )

        assert "quality_gate.json" in artifacts
        assert "boundary_audit.json" in artifacts

    def test_run_cross_border_type(self, orchestrator, mock_job, mock_intake):
        mock_job.assessment_type = AssessmentType.cross_border_data_transfer
        artifacts = orchestrator.run(
            mock_job, "conv_test_001",
            "财务数据需要出境到新加坡",
            "cross_border_data_transfer",
            [], [], mock_intake,
        )

        assert "extracted_facts.json" in artifacts
        assert "prototype_report.md" in artifacts

    def test_run_generates_manifest(self, orchestrator, mock_job, mock_intake):
        artifacts = orchestrator.run(
            mock_job, "conv_test_001",
            "请运行评估",
            "data_transaction_compliance",
            [], [], mock_intake,
        )

        assert "runtime_manifest.json" in artifacts
        manifest_path = artifacts["runtime_manifest.json"]
        real_path = Path("d:/Python/Pycharm/Agent_data/services/backend_api_v2") / manifest_path
        if real_path.exists():
            manifest = json.loads(real_path.read_text(encoding="utf-8"))
            assert manifest["runtime_mode"] == "full_chain_runtime"
            assert manifest["uploaded_files_written_to_chroma"] == False

    def test_run_generates_source_trace(self, orchestrator, mock_job, mock_intake):
        artifacts = orchestrator.run(
            mock_job, "conv_test_001",
            "请运行评估",
            "data_transaction_compliance",
            [], [], mock_intake,
        )

        assert "source_trace.json" in artifacts
        assert "bridge_trace.json" in artifacts

    def test_run_generates_report_content(self, orchestrator, mock_job, mock_intake):
        artifacts = orchestrator.run(
            mock_job, "conv_test_001",
            "请运行数据交易合规评估",
            "data_transaction_compliance",
            [], [], mock_intake,
        )

        assert "prototype_report.md" in artifacts
        report_path = artifacts["prototype_report.md"]
        real_path = Path("d:/Python/Pycharm/Agent_data/services/backend_api_v2") / report_path
        if real_path.exists():
            report = real_path.read_text(encoding="utf-8")
            assert "ReguThink" in report or "非正式法律意见" in report or "合规评估报告" in report

    def test_run_missing_capabilities(self, orchestrator, mock_job, mock_intake):
        artifacts = orchestrator.run(
            mock_job, "conv_test_001",
            "请运行评估",
            "data_transaction_compliance",
            [], [], mock_intake,
        )

        assert "missing_capabilities.json" in artifacts

    def test_run_failure_handling(self, orchestrator, mock_job, mock_intake):
        with patch.object(orchestrator.fact_extractor, 'extract', side_effect=RuntimeError("simulated failure")):
            with pytest.raises(RuntimeError):
                orchestrator.run(
                    mock_job, "conv_test_001",
                    "请运行评估",
                    "data_transaction_compliance",
                    [], [], mock_intake,
                )

    def test_events_emitted(self, orchestrator, mock_job, mock_intake):
        orchestrator.run(
            mock_job, "conv_test_001",
            "请运行评估",
            "data_transaction_compliance",
            [], [], mock_intake,
        )

        events = orchestrator.events.list_events(mock_job.job_id)
        event_types = [e.event_type for e in events]
        assert "job_created" in event_types
        assert "final" in event_types
        assert "material_parsing_started" in event_types or "material_parsing_completed" in event_types
        assert "autojudge_started" in event_types or "autojudge_completed" in event_types

    def test_retrieval_collections(self, orchestrator):
        cols_data = orchestrator._get_collections_for_type("data_transaction_compliance")
        assert "data_transaction" in cols_data
        assert "personal_information" in cols_data

        cols_cb = orchestrator._get_collections_for_type("cross_border_data_transfer")
        assert "cross_border_data_transfer" in cols_cb