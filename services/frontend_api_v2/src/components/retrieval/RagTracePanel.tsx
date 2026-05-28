import type { CaseArtifactsResponse } from "../../types/reguthink-api";
import { asRecord, fieldText, JsonPreview, PanelNote } from "../workspace/artifactUtils";

type RagTracePanelProps = {
  artifacts: CaseArtifactsResponse | null;
};

export function RagTracePanel({ artifacts }: RagTracePanelProps) {
  const trace = asRecord(artifacts?.json_artifacts["retrieval_trace.json"]);

  return (
    <section className="wb-tab-panel">
      <div className="wb-panel-heading">
        <h2>RAG Trace</h2>
        <span>BGE-M3 partially_effective</span>
      </div>
      <PanelNote>BGE-M3 remains partially_effective. Retrieval traces expose caveats and do not resolve source backing.</PanelNote>
      <div className="wb-score-grid">
        <div><span>BGE-M3 status</span><strong>{fieldText(trace, ["bge_m3_status"], "partially_effective")}</strong></div>
        <div><span>vector query</span><strong>{fieldText(trace, ["bge_m3_vector_query_executed", "vector_query_executed"])}</strong></div>
        <div><span>candidate count</span><strong>{fieldText(trace, ["bge_m3_vector_candidate_count", "vector_candidate_count"])}</strong></div>
        <div><span>legacy fallback</span><strong>{fieldText(trace, ["forbidden_legacy_fallback_used"])}</strong></div>
      </div>
      <JsonPreview value={trace} maxHeight={360} />
    </section>
  );
}
