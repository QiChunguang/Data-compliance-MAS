"""Tests for UploadedMaterialRuntimeAdapter."""
from app.services.uploaded_material_fact_extractor import ExtractedFacts, UploadedMaterialFactExtractor
from app.services.assessment_runtime_router import AssessmentRuntimeRouter
from app.services.dynamic_case_profile_builder import DynamicCaseProfileBuilder
from app.services.uploaded_material_runtime_adapter import (
    BoundaryAudit,
    RiskScore,
    UploadedMaterialRuntimeAdapter,
)


def test_adapter_generates_all_artifact_data():
    adapter = UploadedMaterialRuntimeAdapter()
    extractor = UploadedMaterialFactExtractor()
    builder = DynamicCaseProfileBuilder()
    router = AssessmentRuntimeRouter()

    text = "甲方和乙方进行数据交易"
    intake = type("Intake", (), {
        "parties": ["甲方", "乙方"],
        "file_count": 1,
        "model_dump": lambda self, mode=None: {"parties": ["甲方", "乙方"], "file_count": 1},
    })()
    facts = extractor.extract(text, "data_transaction_compliance", intake, [])
    profile = builder.build("data_transaction_compliance", facts, intake, text)
    route = router.route("data_transaction_compliance", text, intake)

    risk = RiskScore(overall_risk_level="medium")
    boundary = BoundaryAudit()

    result = adapter.adapt(
        "conv_test", text, "data_transaction_compliance", [], [], intake,
        facts, profile, route, [], [], risk, boundary, [],
    )

    assert "input_materials_manifest" in result
    assert "uploaded_material_intake" in result
    assert "extracted_facts" in result
    assert "dynamic_case_profile" in result
    assert "runtime_route" in result
    assert "retrieval_trace" in result
    assert "risk_score" in result
    assert "boundary_audit" in result
    assert "missing_capabilities" in result


def test_adapter_boundary_audit_values():
    boundary = BoundaryAudit()
    assert boundary.formal_legal_opinion is False
    assert boundary.source_backed_claim_fabricated is False
    assert boundary.manual_verified_claim_fabricated is False
    assert boundary.uploaded_files_written_to_chroma is False
    assert boundary.uploaded_files_written_to_neo4j is False
    assert boundary.current_backend_modified is False


def test_risk_score_has_required_fields():
    risk = RiskScore(overall_risk_level="high")
    assert risk.overall_risk_level == "high"
    assert hasattr(risk, "transaction_risk")
    assert hasattr(risk, "cross_border_risk")
    assert hasattr(risk, "personal_information_risk")
    assert hasattr(risk, "sensitive_pi_risk")
    assert hasattr(risk, "evidence_gap_risk")


def test_adapter_compliance_analysis():
    adapter = UploadedMaterialRuntimeAdapter()
    extractor = UploadedMaterialFactExtractor()
    text = "涉及个人信息的数据交易"
    intake = type("Intake", (), {"parties": ["甲方"], "file_count": 1})()
    facts = extractor.extract(text, "data_transaction_compliance", intake, [])

    analysis = adapter._build_compliance_analysis("data_transaction_compliance", facts, [])
    assert "findings" in analysis
    assert "recommendations" in analysis
    assert analysis["not_formal_legal_opinion"] is True


def test_adapter_runtime_manifest():
    adapter = UploadedMaterialRuntimeAdapter()
    route = type("Route", (), {"support_level": "full_prototype"})()
    manifest = adapter._build_runtime_manifest(route)
    assert manifest["runtime_mode"] == "uploaded_material_runtime"
    assert len(manifest["stages"]) == 11
    assert manifest["source_backed"] is False