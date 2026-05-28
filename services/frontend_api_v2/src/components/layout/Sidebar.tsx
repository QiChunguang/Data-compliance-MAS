import type { HealthResponse } from "../../types/reguthink-api";

type SidebarProps = {
  activeView: string;
  onSelectView: (view: string) => void;
  health: HealthResponse | null;
};

const NAV_ITEMS = [
  ["workbench", "工作台"],
  ["interactive", "交互评估"],
  ["matrix", "案例矩阵"],
  ["jobs", "运行任务"],
  ["report", "诊断报告"],
  ["evidence", "证据审查"],
  ["citations", "引用计划"],
  ["score", "评分体系"],
  ["rag", "RAG Trace"],
  ["boundaries", "系统边界"],
];

export function Sidebar({ activeView, onSelectView, health }: SidebarProps) {
  return (
    <aside className="wb-sidebar" aria-label="ReguThink primary navigation">
      <div className="wb-brand">
        <div className="wb-brand-mark">RT</div>
        <span>ReguThink</span>
      </div>
      <nav className="wb-nav">
        {NAV_ITEMS.map(([key, label]) => (
          <button
            className={activeView === key ? "wb-nav-item active" : "wb-nav-item"}
            key={key}
            type="button"
            onClick={() => onSelectView(key)}
          >
            <span className="wb-nav-dot" />
            <span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="wb-sidebar-status">
        <span className={health?.ok ? "wb-status-light on" : "wb-status-light"} />
        <strong>{health?.ok ? "backend connected" : "backend disconnected"}</strong>
        <span>prototype</span>
        <span>API v2</span>
      </div>
    </aside>
  );
}
