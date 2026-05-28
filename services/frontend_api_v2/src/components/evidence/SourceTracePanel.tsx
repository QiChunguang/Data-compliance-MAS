import type { CaseArtifactsResponse } from "../../types/reguthink-api";
import { asArray, asRecord, fieldText, JsonPreview, PanelNote } from "../workspace/artifactUtils";

type SourceTracePanelProps = {
  artifacts: CaseArtifactsResponse | null;
};

export function SourceTracePanel({ artifacts }: SourceTracePanelProps) {
  const trace = asRecord(artifacts?.json_artifacts["source_trace.json"]);
  const rows = asArray(trace?.source_trace_rows);

  return (
    <section className="wb-tab-panel">
      <div className="wb-panel-heading">
        <h2>Source Trace</h2>
        <span>trace visibility, not human verification</span>
      </div>
      <PanelNote>Source trace is a diagnostic trace only. It must not be described as manual verification.</PanelNote>
      {rows.length ? (
        <div className="wb-evidence-list">
          {rows.slice(0, 12).map((row, index) => {
            const record = asRecord(row);
            return (
              <article className="wb-evidence-row" key={index}>
                <strong>{fieldText(record, ["source_id", "claim_id", "id"])}</strong>
                <dl>
                  <dt>local_path</dt>
                  <dd>{fieldText(record, ["local_path", "path"])}</dd>
                  <dt>chunk_id</dt>
                  <dd>{fieldText(record, ["chunk_id"])}</dd>
                  <dt>status</dt>
                  <dd>{fieldText(record, ["status", "trace_status"])}</dd>
                  <dt>caveat</dt>
                  <dd>{fieldText(record, ["caveat", "limitation", "limitations"])}</dd>
                </dl>
              </article>
            );
          })}
        </div>
      ) : (
        <JsonPreview value={trace} />
      )}
    </section>
  );
}
