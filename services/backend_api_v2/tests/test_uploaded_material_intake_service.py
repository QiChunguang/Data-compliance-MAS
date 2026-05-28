from app.models.upload import UploadedFile
from app.services.uploaded_material_intake_service import UploadedMaterialIntakeService


def test_intake_no_files():
    service = UploadedMaterialIntakeService()
    intake = service.intake([], "请做数据交易合规评估")
    assert intake.file_count == 0
    assert len(intake.boundary_warnings) == 4
    assert "uploaded files are preview_only/intake_only" in intake.boundary_warnings[0]


def test_intake_with_text_preview():
    service = UploadedMaterialIntakeService()
    file_record = UploadedFile(
        file_id="file_test",
        conversation_id="conv_test",
        original_filename="test_contract.txt",
        stored_path="uploads/conv_test/files/file_test_test_contract.txt",
        display_path="uploads/conv_test/files/file_test_test_contract.txt",
        mime_type="text/plain",
        size_bytes=500,
        sha256="abc123",
        parse_status="parsed",
        text_preview="甲方：某科技有限公司\n乙方：某数据服务有限公司\n涉及个人信息和跨境传输",
    )
    intake = service.intake([file_record], "数据交易合规评估")
    assert intake.file_count == 1
    assert len(intake.file_summaries) == 1
    assert intake.file_summaries[0]["parse_status"] == "parsed"


def test_intake_detects_keywords():
    service = UploadedMaterialIntakeService()
    file_record = UploadedFile(
        file_id="file_test",
        conversation_id="conv_test",
        original_filename="test.txt",
        stored_path="uploads/conv_test/files/file_test_test.txt",
        display_path="uploads/conv_test/files/file_test_test.txt",
        mime_type="text/plain",
        size_bytes=100,
        sha256="abc123",
        parse_status="parsed",
        text_preview="个人信息处理者向境外接收方提供个人信息，需要进行安全评估。涉及敏感个人信息如生物识别。甲方委托乙方处理交易数据。",
    )
    intake = service.intake([file_record], "")
    assert any("个人信息" in p for p in intake.personal_information_indicators)
    assert any("敏感个人信息" in p for p in intake.sensitive_pi_indicators)
    assert len(intake.cross_border_indicators) > 0
    assert any("境外接收方" in p or "安全评估" in p for p in intake.cross_border_indicators)


def test_intake_boundary_warnings_always_present():
    service = UploadedMaterialIntakeService()
    intake = service.intake([], "测试")
    assert len(intake.boundary_warnings) == 4
    warnings_text = " ".join(intake.boundary_warnings)
    assert "preview_only" in warnings_text
    assert "Chroma" in warnings_text
    assert "Neo4j" in warnings_text
    assert "source-backed" in warnings_text
    assert "manual verification" in warnings_text