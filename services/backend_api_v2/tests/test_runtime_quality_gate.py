"""Test RuntimeQualityGateService."""
from __future__ import annotations

import pytest

from app.services.runtime_quality_gate_service import RuntimeQualityGateService, QualityGateResult


class TestRuntimeQualityGate:

    def setup_method(self):
        self.gate = RuntimeQualityGateService()

    def _mock_clean_boundary(self):
        class MockCleanBoundary:
            formal_legal_opinion = False
            source_backed_claim_fabricated = False
            uploaded_files_written_to_chroma = False
            uploaded_files_written_to_neo4j = False
            current_backend_modified = False
            manual_verified_claim_fabricated = False

            def model_dump(self, mode=None):
                return {
                    "formal_legal_opinion": False,
                    "source_backed_claim_fabricated": False,
                    "uploaded_files_written_to_chroma": False,
                    "uploaded_files_written_to_neo4j": False,
                    "current_backend_modified": False,
                    "manual_verified_claim_fabricated": False,
                }
        return MockCleanBoundary()

    def _mock_autojudge(self, score=75.0):
        class MockAutoJudge:
            def __init__(self, s):
                self.overall_score = s
            def model_dump(self, mode=None):
                return {"overall_score": self.overall_score, "grade": "C"}
        return MockAutoJudge(score)

    def test_all_artifacts_present(self):
        artifacts = {name: f"path/{name}" for name in self.gate.REQUIRED_ARTIFACTS}
        result = self.gate.check(artifacts,
                                  autojudge_result=self._mock_autojudge(),
                                  boundary_audit=self._mock_clean_boundary())
        assert result.gate_passed
        assert result.gate_status in ("passed", "pass_with_warnings")

    def test_some_artifacts_missing(self):
        artifacts = {
            "extracted_facts.json": "path/extracted_facts.json",
            "risk_score.json": "path/risk_score.json",
        }
        result = self.gate.check(artifacts)
        assert result.failed_checks > 0
        assert len(result.missing_artifacts) > 0

    def test_autojudge_missing(self):
        artifacts = {name: f"path/{name}" for name in self.gate.REQUIRED_ARTIFACTS if name != "autojudge_result.json"}
        result = self.gate.check(artifacts, autojudge_result=None)
        assert any("autojudge" in c.get("check", "") for c in result.check_results if not c.get("passed", True))

    def test_autojudge_present(self):
        class MockAutoJudge:
            overall_score = 75.0
            def model_dump(self, mode=None):
                return {"overall_score": 75.0, "grade": "C"}

        artifacts = {name: f"path/{name}" for name in self.gate.REQUIRED_ARTIFACTS}
        result = self.gate.check(artifacts, autojudge_result=MockAutoJudge())
        assert any("autojudge" in c.get("check", "") and c.get("passed") for c in result.check_results)

    def test_boundary_violations_detected(self):
        class MockViolation:
            formal_legal_opinion = True
            source_backed_claim_fabricated = True
            uploaded_files_written_to_chroma = True
            uploaded_files_written_to_neo4j = False
            current_backend_modified = False
            manual_verified_claim_fabricated = False

            def model_dump(self, mode=None):
                return {
                    "formal_legal_opinion": True,
                    "source_backed_claim_fabricated": True,
                    "uploaded_files_written_to_chroma": True,
                    "uploaded_files_written_to_neo4j": False,
                    "current_backend_modified": False,
                    "manual_verified_claim_fabricated": False,
                }

        artifacts = {name: f"path/{name}" for name in self.gate.REQUIRED_ARTIFACTS}
        result = self.gate.check(artifacts, boundary_audit=MockViolation())
        assert len(result.boundary_violations) >= 3

    def test_clean_boundary(self):
        class MockClean:
            formal_legal_opinion = False
            source_backed_claim_fabricated = False
            uploaded_files_written_to_chroma = False
            uploaded_files_written_to_neo4j = False
            current_backend_modified = False
            manual_verified_claim_fabricated = False

            def model_dump(self, mode=None):
                return {
                    "formal_legal_opinion": False,
                    "source_backed_claim_fabricated": False,
                    "uploaded_files_written_to_chroma": False,
                    "uploaded_files_written_to_neo4j": False,
                    "current_backend_modified": False,
                    "manual_verified_claim_fabricated": False,
                }

        artifacts = {name: f"path/{name}" for name in self.gate.REQUIRED_ARTIFACTS}
        result = self.gate.check(artifacts, boundary_audit=MockClean())
        assert len(result.boundary_violations) == 0

    def test_quality_gate_required_artifacts_list(self):
        required = self.gate.REQUIRED_ARTIFACTS
        assert "extracted_facts.json" in required
        assert "autojudge_result.json" in required
        assert "quality_gate.json" in required
        assert "prototype_report.md" in required
        assert len(required) >= 15