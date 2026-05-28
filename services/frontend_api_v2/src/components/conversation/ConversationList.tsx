import type { Conversation } from "../../types/reguthink-interactive-api";

type Props = {
  conversations: Conversation[];
  selectedId: string;
  loading: boolean;
  onCreate: () => void;
  onSelect: (conversationId: string) => void;
  showAll: boolean;
  onToggleShowAll: () => void;
};

export function ConversationList({ conversations, selectedId, loading, onCreate, onSelect, showAll, onToggleShowAll }: Props) {
  const visibleConversations = showAll ? conversations : conversations.slice(0, 5);
  
  return (
    <aside className="wb-case-rail interactive-rail">
      <button className="wb-new-diagnostic" type="button" onClick={onCreate}>
        新建交互评估
      </button>
      <div className="wb-rail-meta">
        <span>Conversations</span>
        <span>{loading ? "loading" : conversations.length}</span>
      </div>
      <div className="wb-case-list">
        {visibleConversations.map((item) => (
          <button
            className={item.conversation_id === selectedId ? "wb-case-card active" : "wb-case-card"}
            key={item.conversation_id}
            type="button"
            onClick={() => onSelect(item.conversation_id)}
          >
            <span className="wb-case-id">{item.title}</span>
            <span className="wb-case-weakness">{item.assessment_type}</span>
            <span className="wb-case-row">
              <span>{item.message_count} messages</span>
              <span>{item.file_count} files</span>
            </span>
          </button>
        ))}
      </div>
      {conversations.length > 5 && (
        <button className="show-more-btn" type="button" onClick={onToggleShowAll}>
          {showAll ? "收起历史会话" : `展开全部 ${conversations.length} 个会话`}
        </button>
      )}
      <div className="wb-panel-note compact">
        上传文件只进入 runtime_storage。上传材料不等于 source-backed，也不等于人工核验。
      </div>
    </aside>
  );
}
