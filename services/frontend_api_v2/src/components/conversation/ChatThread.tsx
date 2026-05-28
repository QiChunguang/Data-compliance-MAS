import type { Message } from "../../types/reguthink-interactive-api";
import { ChatMessageBubble } from "./ChatMessageBubble";

export function ChatThread({ messages }: { messages: Message[] }) {
  if (messages.length === 0) {
    return (
      <div className="chat-empty">
        <h2>您好，有什么可以帮您？</h2>
        <p>请上传业务材料，或直接输入合规问题开始辅助分析。</p>
      </div>
    );
  }

  return (
    <section className="chat-thread" aria-label="conversation messages">
      {messages.map((message) => (
        <ChatMessageBubble key={message.message_id} message={message} />
      ))}
    </section>
  );
}
