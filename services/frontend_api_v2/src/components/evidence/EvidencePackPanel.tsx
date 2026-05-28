import type { CaseArtifactsResponse } from "../../types/reguthink-api";
import { asArray, asRecord, fieldText, JsonPreview, PanelNote } from "../workspace/artifactUtils";

type EvidencePackPanelProps = {
  artifacts: CaseArtifactsResponse | null;
};

export function EvidencePackPanel({ artifacts }: EvidencePackPanelProps) {
  const pack = asRecord(artifacts?.json_artifacts["evidence_pack.json"]);
  const rows = asArray(pack?.evidence_rows);

  return (
    <section className="wb-tab-panel">
      <div className="wb-panel-heading">
        <h2>Evidence Pack</h2>
        <span>source-backed / manual / article-level verification are not claimed</span>
      </div>
      <PanelNote>
        Evidence gaps and missing business materials must remain visible. Missing fields are shown as missing / placeholder.
      </PanelNote>
      {rows.length ? (
        <div className="wb-evidence-list">
          {rows.slice(0, 12).map((row, index) => {
            const record = asRecord(row);
            return (
              <article className="wb-evidence-row" key={index}>
                <strong>{fieldText(record, ["source_id", "source_name", "title"])}</strong>
                <dl>
                  <dt>chunk_id</dt>
                  <dd>{fieldText(record, ["chunk_id", "id"])}</dd>
                  <dt>local_path</dt>
                  <dd>{fieldText(record, ["local_path", "path"])}</dd>
                  <dt>support_role</dt>
                  <dd>{fieldText(record, ["support_role", "role"])}</dd>
                  <dt>support_strength</dt>
                  <dd>{fieldText(record, ["support_strength", "strength"])}</dd>
                  <dt>limitations</dt>
                  <dd>{fieldText(record, ["limitations", "limitation", "evidence_boundary"])}</dd>
                </dl>
              </article>
            );
          })}
        </div>
      ) : (
        <JsonPreview value={pack} />
      )}
    </section>
  );
}
