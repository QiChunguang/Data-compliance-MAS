import type {
  BaselineStatusResponse,
  CaseArtifactsResponse,
  CaseSummary,
  HealthResponse,
  ReportResponse,
} from "../../types/reguthink-api";
import { BoundaryPanel } from "../boundaries/BoundaryPanel";
import { CitationPlanPanel } from "../evidence/CitationPlanPanel";
import { EvidencePackPanel } from "../evidence/EvidencePackPanel";
import { SourceTracePanel } from "../evidence/SourceTracePanel";
import { DiagnosticReportPanel } from "../report/DiagnosticReportPanel";
import { BgeM3StatusPanel } from "../retrieval/BgeM3StatusPanel";
import { RagTracePanel } from "../retrieval/RagTracePanel";
import { RerankerStatusPanel } from "../retrieval/RerankerStatusPanel";
import { LlmJudgePanel } from "../scoring/LlmJudgePanel";
import { ScoreBreakdownPanel } from "../scoring/ScoreBreakdownPanel";

type DiagnosticWorkspaceProps = {
  selectedCase: CaseSummary | null;
  artifacts: CaseArtifactsResponse | null;
  report: ReportResponse | null;
  health: HealthResponse | null;
  baseline: BaselineStatusResponse | null;
  activeTab: string;
  reportLoading: boolean;
  reportError: string | null;
  onTabChange: (tab: string) => void;
  onWelcomeAction: (tab: string) => void;
};

const TABS = [
  ["overview", "Overview"],
  ["report", "Report"],
  ["evidence", "Evidence"],
  ["citations", "Citations"],
  ["score", "Score"],
  ["rag", "RAG Trace"],
  ["source", "Source Trace"],
  ["llm", "LLM Judge"],
  ["boundaries", "Boundaries"],
];

const WELCOME_CARDS = [
  ["overview", "查看 18-case 诊断矩阵", "打开当前 full18 分数和弱点总览。"],
  ["score", "审查低分 case", "聚焦 <70、CAP、score gap 和 evidence gap。"],
  ["evidence", "查看证据与引用链", "进入 evidence / citation / source trace 工作流。"],
  ["boundaries", "查看评分与边界说明", "确认 prototype、BGE-M3、reranker 和人工复核边界。"],
];

export function DiagnosticWorkspace({
  selectedCase,
  artifacts,
  report,
  health,
  baseline,
  activeTab,
  reportLoading,
  reportError,
  onTabChange,
  onWelcomeAction,
}: DiagnosticWorkspaceProps) {
  return (
    <div className="wb-workspace">
      <section className="wb-welcome" aria-label="workbench welcome state">
        <div>
          <p className="wb-eyebrow">ReguThink diagnostic workbench</p>
          <h1>您好，有什么可以帮您？</h1>
          <p>当前系统为 prototype diagnostic，不是正式法律意见。低分、CAP、evidence gap 与 source trace caveat 会常驻展示。</p>
        </div>
        <div className="wb-welcome-cards">
          {WELCOME_CARDS.map(([tab, title, body]) => (
            <button key={tab} type="button" onClick={() => onWelcomeAction(tab)}>
              <strong>{title}</strong>
              <span>{body}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="wb-case-overview">
        <div className="wb-overview-title">
          <span>Selected diagnostic</span>
          <strong>{selectedCase?.case_id ?? "no case selected"}</strong>
        </div>
        <div className="wb-score-grid compact">
          <div><span>final_score</span><strong>{selectedCase?.final_score ?? "missing"}</strong></div>
          <div><span>programmatic</span><strong>{selectedCase?.programmatic_score ?? "missing"}</strong></div>
          <div><span>LLM</span><strong>{selectedCase?.llm_score ?? "missing"}</strong></div>
          <div><span>grade</span><strong>{selectedCase?.grade ?? "missing"}</strong></div>
          <div><span>&gt;=70</span><strong>{selectedCase?.ge_70 ? "yes" : "no / warning"}</strong></div>
          <div><span>BGE-M3</span><strong>{selectedCase?.bge_m3_status ?? "partially_effective"}</strong></div>
        </div>
        <div className="wb-overview-cause">
          <strong>Main cause</strong>
          <span>{selectedCase?.main_issue ?? "missing / placeholder"}</span>
        </div>
        <div className="wb-overview-cause">
          <strong>Artifact path</strong>
          <span>{artifacts?.case_dir ?? "missing / placeholder"}</span>
        </div>
      </section>

      <nav className="wb-tabs" aria-label="workspace tabs">
        {TABS.map(([key, label]) => (
          <button className={activeTab === key ? "active" : ""} key={key} type="button" onClick={() => onTabChange(key)}>
            {label}
          </button>
        ))}
      </nav>

      <section className="wb-panel-map" aria-label="visible workbench panel map">
        <span>Report panel visible</span>
        <span>Evidence panel visible</span>
        <span>Citations panel visible</span>
        <span>Score breakdown visible</span>
        <span>RAG Trace panel visible</span>
        <span>Source Trace panel visible</span>
        <span>LLM Judge panel visible</span>
        <span>Boundary panel visible</span>
      </section>

      {activeTab === "overview" && (
        <section className="wb-tab-panel">
          <div className="wb-panel-heading">
            <h2>Overview</h2>
            <span>18-case matrix entry / diagnostic summary</span>
          </div>
          <div className="wb-mini-grid">
            <BgeM3StatusPanel artifacts={artifacts} />
            <RerankerStatusPanel artifacts={artifacts} />
          </div>
          <BoundaryPanel health={health} baseline={baseline} />
        </section>
      )}
      {activeTab === "report" && <DiagnosticReportPanel report={report} loading={reportLoading} error={reportError} />}
      {activeTab === "evidence" && <EvidencePackPanel artifacts={artifacts} />}
      {activeTab === "citations" && <CitationPlanPanel artifacts={artifacts} />}
      {activeTab === "score" && <ScoreBreakdownPanel selectedCase={selectedCase} artifacts={artifacts} />}
      {activeTab === "rag" && <RagTracePanel artifacts={artifacts} />}
      {activeTab === "source" && <SourceTracePanel artifacts={artifacts} />}
      {activeTab === "llm" && <LlmJudgePanel artifacts={artifacts} />}
      {activeTab === "boundaries" && <BoundaryPanel health={health} baseline={baseline} />}
    </div>
  );
}
