"""Tests for DynamicCaseProfileBuilder."""
from app.services.dynamic_case_profile_builder import DynamicCaseProfileBuilder
from app.services.uploaded_material_fact_extractor import ExtractedFacts, UploadedMaterialFactExtractor


def test_build_profile_data_transaction():
    builder = DynamicCaseProfileBuilder()
    extractor = UploadedMaterialFactExtractor()
    text = "甲方和乙方进行数据交易，涉及个人信息"
    intake = type("Intake", (), {"parties": ["甲方", "乙方"], "file_count": 1, "cross_border_indicators": []})()

    facts = extractor.extract(text, "data_transaction_compliance", intake, [])
    profile = builder.build("data_transaction_compliance", facts, intake, text)

    assert profile.case_origin == "uploaded_material_runtime"
    assert "data_transaction" in profile.case_id
    assert len(profile.scenario_tags) > 0
    assert "个人信息保护法" in profile.legal_domains
    assert len(profile.risk_dimensions) > 0
    assert len(profile.limitations) > 0
    assert "prototype_diagnostic" in str(profile.limitations)


def test_build_profile_cross_border():
    builder = DynamicCaseProfileBuilder()
    extractor = UploadedMaterialFactExtractor()
    text = "数据需要出境到境外接收方"
    intake = type("Intake", (), {"parties": [], "file_count": 1, "cross_border_indicators": ["出境"]})()

    facts = extractor.extract(text, "cross_border_data_transfer", intake, [])
    profile = builder.build("cross_border_data_transfer", facts, intake, text)

    assert "cross_border" in profile.case_id
    assert "cross_border" in [t for t in profile.scenario_tags]
    assert any("出境" in d for d in profile.legal_domains)


def test_build_profile_with_sensitive_pi():
    builder = DynamicCaseProfileBuilder()
    extractor = UploadedMaterialFactExtractor()
    text = "涉及金融账户和生物识别等敏感个人信息"
    intake = type("Intake", (), {"parties": [], "file_count": 1})()

    facts = extractor.extract(text, "data_transaction_compliance", intake, [])
    profile = builder.build("data_transaction_compliance", facts, intake, text)

    assert "sensitive_pi" in profile.case_id or "sensitive" in str(profile.scenario_tags).lower()
    assert len(profile.claim_plan_hints) > 0


def test_profile_has_all_required_fields():
    builder = DynamicCaseProfileBuilder()
    extractor = UploadedMaterialFactExtractor()
    text = "测试评估"
    intake = type("Intake", (), {"parties": [], "file_count": 0})()

    facts = extractor.extract(text, "data_transaction_compliance", intake, [])
    profile = builder.build("data_transaction_compliance", facts, intake, text)

    assert profile.case_id
    assert profile.assessment_type
    assert profile.facts is not None
    assert profile.legal_domains is not None
    assert profile.uploaded_material_trace is not None
    assert len(profile.report_sections) > 0