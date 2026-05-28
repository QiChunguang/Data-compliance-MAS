from app.models.assessment import AssessmentType
from app.services.assessment_intent_service import AssessmentIntentService


def test_detect_transaction_intent():
    service = AssessmentIntentService()
    intent = service.detect("请帮我做数据交易合规评估，评估数据买卖中的法律风险。")
    assert intent.detected_type == AssessmentType.data_transaction_compliance
    assert intent.confidence in ("high", "medium", "low")


def test_detect_cross_border_intent():
    service = AssessmentIntentService()
    intent = service.detect("需要评估跨境数据传输的安全性和合规性。")
    assert intent.detected_type == AssessmentType.cross_border_data_transfer


def test_detect_pipl_intent():
    service = AssessmentIntentService()
    intent = service.detect("请评估个人信息处理是否符合PIPL要求。")
    assert intent.detected_type == AssessmentType.pipl_personal_information_protection


def test_explicit_type_overrides_detection():
    service = AssessmentIntentService()
    intent = service.detect("数据交易", AssessmentType.cross_border_data_transfer)
    assert intent.detected_type == AssessmentType.cross_border_data_transfer
    assert intent.confidence == "explicit"


def test_empty_message_defaults_to_general():
    service = AssessmentIntentService()
    intent = service.detect("你好")
    assert intent.detected_type == AssessmentType.general_data_compliance_diagnostic
    assert intent.confidence == "low"