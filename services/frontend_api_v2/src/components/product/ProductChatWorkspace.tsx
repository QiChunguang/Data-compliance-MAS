import React from 'react';
import { ProductWelcomePanel } from './ProductWelcomePanel';
import { ChatThread } from '../conversation/ChatThread';
import type { Message } from '../../types/reguthink-interactive-api';

type ProductChatWorkspaceProps = {
  hasConversation: boolean;
  messages: Message[];
  onSelectAssessment: (type: string) => void;
};

export const ProductChatWorkspace: React.FC<ProductChatWorkspaceProps> = ({
  hasConversation,
  messages,
  onSelectAssessment,
}) => {
  return (
    <main className="product-chat-workspace">
      <div className="product-chat-header">
        <h2 className="product-chat-title">ReguThink 数据合规智能体</h2>
        <div className="product-chat-header-badges">
          <span className="product-badge info">知识库已连接</span>
          <span className="product-badge success">审查服务正常</span>
        </div>
      </div>

      <div className="product-chat-content">
        {!hasConversation ? (
          <div className="product-chat-messages" data-testid="chat-thread">
            <div data-testid="chat-hero">
              <ProductWelcomePanel onSelectAssessment={onSelectAssessment} />
            </div>
          </div>
        ) : (
          <div className="product-chat-messages" data-testid="chat-thread">
            <ChatThread messages={messages} />
          </div>
        )}
      </div>
    </main>
  );
};
