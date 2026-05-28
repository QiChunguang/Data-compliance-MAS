import type { CaseArtifactsResponse } from "../../types/reguthink-api";
import { asRecord, fieldText } from "../workspace/artifactUtils";

type RerankerStatusPanelProps = {
  artifacts: CaseArtifactsResponse | null;
};

export function RerankerStatusPanel({ artifacts }: RerankerStatusPanelProps) {
  const trace = asRecord(artifacts?.json_artifacts["retrieval_trace.json"]);
  return (
    <article className="wb-mini-panel">
      <h3>Reranker Status</h3>
      <p>local neural reranker = diagnostic_only / disabled by default</p>
      <dl>
        <dt>loaded</dt>
        <dd>{fieldText(trace, ["local_neural_reranker_loaded"])}</dd>
        <dt>used in runtime</dt>
        <dd>{fieldText(trace, ["local_neural_reranker_used_in_runtime"])}</dd>
      </dl>
    </article>
  );
}
