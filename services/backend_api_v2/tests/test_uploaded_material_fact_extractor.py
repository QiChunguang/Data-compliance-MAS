"""Tests for UploadedMaterialFactExtractor."""
from app.services.uploaded_material_fact_extractor import ExtractedFacts, UploadedMaterialFactExtractor


def test_extract_parties_from_text():
    extractor = UploadedMaterialFactExtractor()
    text = "甲方：数据科技有限公司\n乙方：数据接收平台有限公司"
    intake = type("Intake", (), {"parties": []})()

    facts = extractor.extract(text, "data_transaction_compliance", intake, [])
    assert len(facts.parties) >= 2
    assert any("甲方" in p for p in facts.parties)
    assert any("乙方" in p for p in facts.parties)


def test_extract_personal_information():
    extractor = UploadedMaterialFactExtractor()
    text = "本次交易涉及大量个人信息和用户数据"
    intake = type("Intake", (), {"parties": []})()

    facts = extractor.extract(text, "data_transaction_compliance", intake, [])
    assert len(facts.personal_information_categories) > 0
    assert "个人信息" in facts.personal_information_categories


def test_extract_sensitive_pi():
    extractor = UploadedMaterialFactExtractor()
    text = "包含金融账户和生物识别等敏感个人信息"
    intake = type("Intake", (), {"parties": []})()

    facts = extractor.extract(text, "data_transaction_compliance", intake, [])
    assert len(facts.sensitive_pi_categories) >= 2
    assert "金融账户" in facts.sensitive_pi_categories or "生物识别" in facts.sensitive_pi_categories


def test_extract_cross_border():
    extractor = UploadedMaterialFactExtractor()
    text = "该数据需要出境至境外接收方进行跨境处理"
    intake = type("Intake", (), {"parties": [], "cross_border_indicators": ["跨境"]})()

    facts = extractor.extract(text, "cross_border_data_transfer", intake, [])
    assert len(facts.cross_border_elements) >= 2
    assert "出境" in facts.cross_border_elements
    assert facts.transfer_direction == "cross_border_export"


def test_extract_consent_and_contract():
    extractor = UploadedMaterialFactExtractor()
    text = "用户已签署用户协议并授权数据处理"
    intake = type("Intake", (), {"parties": []})()

    facts = extractor.extract(text, "data_transaction_compliance", intake, [])
    assert facts.consent_status == "mentioned"
    assert facts.contract_status == "mentioned"


def test_missing_facts_detection():
    extractor = UploadedMaterialFactExtractor()
    text = "测试评估"
    intake = type("Intake", (), {"parties": []})()

    facts = extractor.extract(text, "data_transaction_compliance", intake, [])
    assert len(facts.missing_facts) > 0


def test_extraction_confidence():
    extractor = UploadedMaterialFactExtractor()
    rich_text = "甲方和乙方签订数据交易合同，涉及个人信息，用户已授权同意，采取了加密安全措施"
    intake = type("Intake", (), {"parties": ["甲方", "乙方"]})()

    facts = extractor.extract(rich_text, "data_transaction_compliance", intake, [])
    assert facts.extraction_confidence in ("low", "medium", "high")
    assert facts.consent_status == "mentioned"
    assert len(facts.security_measures) > 0


def test_data_categories():
    extractor = UploadedMaterialFactExtractor()
    text = "财务数据和交易数据"
    intake = type("Intake", (), {"parties": []})()

    facts = extractor.extract(text, "data_transaction_compliance", intake, [])
    assert "financial_data" in facts.data_categories