from app.models.chat import CreateConversationRequest, CreateMessageRequest
from app.services.conversation_service import ConversationService


def test_create_conversation_and_message():
    service = ConversationService()
    conversation = service.create_conversation(CreateConversationRequest(title="BE2 test"))
    assert conversation.conversation_id.startswith("conv_")

    message = service.add_message(
        conversation.conversation_id,
        CreateMessageRequest(content="Please run a diagnostic.", attachments=[]),
    )
    assert message.message_id.startswith("msg_")
    assert message.conversation_id == conversation.conversation_id

    messages = service.list_messages(conversation.conversation_id)
    assert any(item.message_id == message.message_id for item in messages)
