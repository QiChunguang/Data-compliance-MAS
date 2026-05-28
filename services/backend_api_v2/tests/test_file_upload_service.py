from io import BytesIO
import asyncio

from fastapi import UploadFile

from app.models.chat import CreateConversationRequest
from app.services.conversation_service import ConversationService
from app.services.file_upload_service import FileUploadService, UploadValidationError


def make_upload(filename: str, content: bytes = b"hello") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content), headers=None)


def save(service: FileUploadService, conversation_id: str, filename: str, content: bytes = b"hello"):
    return asyncio.run(service.save_upload(conversation_id, make_upload(filename, content)))


def test_sanitize_required_filenames():
    service = FileUploadService()
    assert service.sanitize_filename("../evil.txt") == "evil.txt"
    assert service.sanitize_filename("..\\evil.txt") == "evil.txt"
    assert service.sanitize_filename("C:\\Windows\\test.txt") == "test.txt"
    assert service.sanitize_filename("中文 文件名.md") == "中文 文件名.md"
    assert service.sanitize_filename("重复文件名.txt") == "重复文件名.txt"


def test_upload_txt_sha256_and_relative_path():
    conversation = ConversationService().create_conversation(CreateConversationRequest(title="upload test"))
    uploaded = save(FileUploadService(), conversation.conversation_id, "../evil.txt", b"hello")

    assert uploaded.original_filename == "../evil.txt"
    assert uploaded.stored_path.startswith("uploads/")
    assert ":" not in uploaded.stored_path
    assert not uploaded.stored_path.startswith("/")
    assert uploaded.sha256 == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert uploaded.parse_status == "parsed"


def test_reject_empty_and_unsupported_file():
    conversation = ConversationService().create_conversation(CreateConversationRequest(title="reject test"))
    service = FileUploadService()

    try:
        save(service, conversation.conversation_id, "empty.txt", b"")
        assert False, "empty upload should fail"
    except UploadValidationError:
        pass

    try:
        save(service, conversation.conversation_id, "evil.exe", b"hello")
        assert False, "unsupported extension should fail"
    except UploadValidationError:
        pass


def test_duplicate_filenames_get_unique_stored_paths():
    conversation = ConversationService().create_conversation(CreateConversationRequest(title="duplicate test"))
    service = FileUploadService()
    first = save(service, conversation.conversation_id, "重复文件名.txt", b"one")
    second = save(service, conversation.conversation_id, "重复文件名.txt", b"two")
    assert first.original_filename == second.original_filename
    assert first.stored_path != second.stored_path
