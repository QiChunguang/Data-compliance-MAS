import type { Message } from "../../types/reguthink-interactive-api";

function formatMarkdown(text: string): string {
  // Simple markdown formatting for display
  return text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^- (.*$)/gim, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n/g, '<br/>');
}

export function ChatMessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  return (
    <article className={`chat-bubble ${message.role}`}>
      <div className="chat-bubble-meta">
        <span className="chat-bubble-role">
          {isUser ? 'You' : isAssistant ? 'ReguThink Agent' : message.role}
        </span>
        <span className="chat-bubble-time">
          {new Date(message.created_at).toLocaleTimeString()}
        </span>
      </div>
      <div
        className="chat-bubble-content"
        dangerouslySetInnerHTML={{ __html: formatMarkdown(message.content) }}
      />
      {message.attachments.length > 0 && (
        <div className="chat-bubble-attachments">
          <span className="wb-chip">attachments: {message.attachments.join(", ")}</span>
        </div>
      )}
    </article>
  );
}
