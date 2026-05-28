import type { CaseArtifactsResponse } from "../../types/reguthink-api";
import { asArray, asRecord, fieldText, JsonPreview, PanelNote } from "../workspace/artifactUtils";

type CitationPlanPanelProps = {
  artifacts: CaseArtifactsResponse | null;
};

export function CitationPlanPanel({ artifacts }: CitationPlanPanelProps) {
  const plan = asRecord(artifacts?.json_artifacts["citation_plan.json"]);
  const citations = asArray(plan?.citations);

  return (
    <section className="wb-tab-panel">
      <div className="wb-panel-heading">
        <h2>Citation Plan</h2>
        <span>selected / rejected reasons remain diagnostic</span>
      </div>
      <PanelNote>引用计划不等于人工核验；selected/rejected 只表示当前诊断链路的机器选择状态。</PanelNote>
      {citations.length ? (
        <div className="wb-evidence-list">
          {citations.slice(0, 12).map((citation, index) => {
            const record = asRecord(citation);
            const selected = fieldText(record, ["selected", "is_selected"], "missing / placeholder");
            return (
              <article className="wb-evidence-row" key={index}>
                <strong>{fieldText(record, ["citation_id", "id", "source_id"])}</strong>
                <dl>
                  <dt>selected</dt>
                  <dd>{selected}</dd>
                  <dt>rejected</dt>
                  <dd>{selected === "False" || selected === "false" ? "true" : fieldText(record, ["rejected"])}</dd>
                  <dt>why_selected</dt>
                  <dd>{fieldText(record, ["why_selected", "selection_reason", "reason"])}</dd>
                  <dt>why_rejected</dt>
                  <dd>{fieldText(record, ["why_rejected", "rejection_reason"])}</dd>
                </dl>
              </article>
            );
          })}
        </div>
      ) : (
        <JsonPreview value={plan} />
      )}
    </section>
  );
}
