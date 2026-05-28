import type { CaseArtifactsResponse } from "../../types/reguthink-api";
import { asRecord, fieldText } from "../workspace/artifactUtils";

type BgeM3StatusPanelProps = {
  artifacts: CaseArtifactsResponse | null;
};

export function BgeM3StatusPanel({ artifacts }: BgeM3StatusPanelProps) {
  const trace = asRecord(artifacts?.json_artifacts["retrieval_trace.json"]);
  return (
    <article className="wb-mini-panel">
      <h3>BGE-M3 Status</h3>
      <p>BGE-M3 = partially_effective</p>
      <dl>
        <dt>device</dt>
        <dd>{fieldText(trace, ["bge_m3_effective_device"])}</dd>
        <dt>embedding dim</dt>
        <dd>{fieldText(trace, ["bge_m3_embedding_dim"])}</dd>
      </dl>
    </article>
  );
}
