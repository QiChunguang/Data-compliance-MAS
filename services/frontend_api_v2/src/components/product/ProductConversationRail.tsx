import React from 'react';
import type { Conversation } from '../../types/reguthink-interactive-api';

type ProductConversationRailProps = {
  conversations: Conversation[];
  selectedId: string;
  loading: boolean;
  onCreate: () => void;
  onSelect: (id: string) => void;
  showAll: boolean;
  onToggleShowAll: () => void;
};

export const ProductConversationRail: React.FC<ProductConversationRailProps> = ({
  conversations,
  selectedId,
  loading,
  onCreate,
  onSelect,
  showAll,
  onToggleShowAll,
}) => {
  // Separate test conversations
  const testConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes('test')
  );
  const regularConversations = conversations.filter((c) =>
    !c.title.toLowerCase().includes('test')
  );

  // Show only 5 regular conversations by default
  const visibleRegular = showAll
    ? regularConversations
    : regularConversations.slice(0, 5);

  return (
    <aside className="product-conversation-rail" data-testid="conversation-rail">
      <div className="product-rail-header">
        <h2 className="product-rail-title">会话</h2>
        <button className="product-new-conversation-btn" type="button" onClick={onCreate}>
          + 新建评估
        </button>
      </div>

      <div className="product-conversation-list">
        {loading ? (
          <div className="product-conversation-loading">加载中...</div>
        ) : (
          <>
            {/* Regular conversations */}
            {visibleRegular.map((conv) => (
              <button
                key={conv.conversation_id}
                className={`product-conversation-item ${selectedId === conv.conversation_id ? 'active' : ''}`}
                type="button"
                onClick={() => onSelect(conv.conversation_id)}
              >
                <div className="product-conversation-title">{conv.title}</div>
                <div className="product-conversation-meta">
                  <span>{conv.message_count} 消息</span>
                  <span>{conv.file_count} 文件</span>
                </div>
              </button>
            ))}

            {/* Toggle button */}
            {regularConversations.length > 5 && (
              <button
                className="product-toggle-conversations-btn"
                type="button"
                onClick={onToggleShowAll}
              >
                {showAll ? '收起历史会话' : `展开全部 ${regularConversations.length} 个会话`}
              </button>
            )}

            {/* Test conversations - collapsed by default */}
            {testConversations.length > 0 && (
              <div className="product-test-conversations">
                <div className="product-test-conversations-title">历史测试会话</div>
                {showAll &&
                  testConversations.map((conv) => (
                    <button
                      key={conv.conversation_id}
                      className={`product-conversation-item test ${selectedId === conv.conversation_id ? 'active' : ''}`}
                      type="button"
                      onClick={() => onSelect(conv.conversation_id)}
                    >
                      <div className="product-conversation-title">{conv.title}</div>
                      <div className="product-conversation-meta">
                        <span>{conv.message_count} 消息</span>
                        <span>{conv.file_count} 文件</span>
                      </div>
                    </button>
                  ))}
              </div>
            )}
          </>
        )}
      </div>
    </aside>
  );
};
