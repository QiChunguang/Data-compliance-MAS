"""Tests for AssessmentRuntimeRouter."""
from app.services.assessment_runtime_router import AssessmentRuntimeRouter


def test_route_data_transaction():
    router = AssessmentRuntimeRouter()
    intake = type("Intake", (), {"cross_border_indicators": []})()
    route = router.route("data_transaction_compliance", "数据交易合规评估", intake)

    assert route.route == "data_transaction"
    assert route.support_level == "full_prototype"
    assert len(route.selected_agents) >= 5
    assert len(route.missing_capabilities) == 0


def test_route_cross_border():
    router = AssessmentRuntimeRouter()
    intake = type("Intake", (), {"cross_border_indicators": ["出境"]})()
    route = router.route("cross_border_data_transfer", "跨境数据", intake)

    assert route.route == "cross_border"
    assert route.support_level == "full_prototype"
    assert len(route.selected_legal_domains) >= 3


def test_route_auto_detect_cross_border():
    router = AssessmentRuntimeRouter()
    intake = type("Intake", (), {"cross_border_indicators": []})()
    route = router.route("data_transaction_compliance", "数据需要出境到境外", intake)

    assert route.route == "cross_border"


def test_route_pipl_limited():
    router = AssessmentRuntimeRouter()
    intake = type("Intake", (), {"cross_border_indicators": []})()
    route = router.route("pipl_personal_information_protection", "个人信息保护", intake)

    assert route.support_level == "limited_prototype"
    assert len(route.missing_capabilities) > 0


def test_route_general_unsupported():
    router = AssessmentRuntimeRouter()
    intake = type("Intake", (), {"cross_border_indicators": []})()
    route = router.route("general_data_compliance_diagnostic", "通用合规", intake)

    assert route.support_level == "unsupported"
    assert len(route.missing_capabilities) > 0