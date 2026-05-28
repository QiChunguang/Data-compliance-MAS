import type { CaseArtifactsResponse, CaseSummary } from "../../types/reguthink-api";
import { asRecord, fieldText, JsonPreview, PanelNote } from "../workspace/artifactUtils";

type ScoreBreakdownPanelProps = {
  selectedCase: CaseSummary | null;
  artifacts: CaseArtifactsResponse | null;
};

export function ScoreBreakdownPanel({ selectedCase, artifacts }: ScoreBreakdownPanelProps) {
  const strict = asRecord(artifacts?.json_artifacts["strict_autojudge_result.json"]);
  const breakdown = strict?.score_component_breakdown ?? artifacts?.json_artifacts["score_component_breakdown.json"];

  return (
    <section className="wb-tab-panel">
      <div className="wb-panel-heading">
        <h2>Score Breakdown</h2>
        <span>programmatic / LLM / cap / reason</span>
      </div>
      <PanelNote>Do not show final_score alone. CAP, score disagreement, and evidence gap reasons stay visible.</PanelNote>
      <div className="wb-score-grid">
        <div><span>final_score</span><strong>{selectedCase?.final_score ?? fieldText(strict, ["final_total_score"])}</strong></div>
        <div><span>programmatic</span><strong>{selectedCase?.programmatic_score ?? fieldText(strict, ["programmatic_score"])}</strong></div>
        <div><span>LLM</span><strong>{selectedCase?.llm_score ?? fieldText(strict, ["llm_semantic_score"])}</strong></div>
        <div><span>grade</span><strong>{selectedCase?.grade ?? fieldText(strict, ["grade"])}</strong></div>
        <div><span>cap</span><strong>{fieldText(strict, ["programmatic_cap", "score_cap_applied"])}</strong></div>
        <div><span>reason</span><strong>{fieldText(strict, ["disagreement_resolution", "unsupported_claim_risk_label"])}</strong></div>
      </div>
      <JsonPreview value={breakdown ?? strict} maxHeight={360} />
    </section>
  );
}
