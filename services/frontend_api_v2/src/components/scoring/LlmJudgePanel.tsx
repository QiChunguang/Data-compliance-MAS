import type { CaseArtifactsResponse } from "../../types/reguthink-api";
import { asRecord, fieldText, JsonPreview, PanelNote } from "../workspace/artifactUtils";

type LlmJudgePanelProps = {
  artifacts: CaseArtifactsResponse | null;
};

export function LlmJudgePanel({ artifacts }: LlmJudgePanelProps) {
  const judge = asRecord(artifacts?.json_artifacts["llm_semantic_judge.json"]);

  return (
    <section className="wb-tab-panel">
      <div className="wb-panel-heading">
        <h2>LLM Judge</h2>
        <span>semantic diagnostic only</span>
      </div>
      <PanelNote>LLM judge output is not human review and cannot fabricate manual_verified or article_level_verified.</PanelNote>
      <div className="wb-score-grid">
        <div><span>judge model</span><strong>{fieldText(judge, ["judge_model"])}</strong></div>
        <div><span>completed</span><strong>{fieldText(judge, ["judge_completed"])}</strong></div>
        <div><span>semantic score</span><strong>{fieldText(judge, ["overall_semantic_score"])}</strong></div>
        <div><span>should be capped</span><strong>{fieldText(judge, ["should_be_capped"])}</strong></div>
      </div>
      <JsonPreview value={judge} maxHeight={360} />
    </section>
  );
}
