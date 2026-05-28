import type { BaselineStatusResponse, HealthResponse } from "../../types/reguthink-api";
import { PanelNote } from "../workspace/artifactUtils";

type BoundaryPanelProps = {
  health: HealthResponse | null;
  baseline: BaselineStatusResponse | null;
};

export function BoundaryPanel({ health, baseline }: BoundaryPanelProps) {
  const flags = baseline?.boundary_flags ?? health?.boundary_flags;
  const rules = baseline?.immutability_rules ?? health?.immutability_rules;

  return (
    <section className="wb-tab-panel">
      <div className="wb-panel-heading">
        <h2>System Boundaries</h2>
        <span>persistent diagnostic guardrails</span>
      </div>
      <PanelNote>Do not hide low scores, CAP, evidence gaps, source trace caveats, or missing business materials.</PanelNote>
      <div className="wb-boundary-grid">
        <span>not_production_ready = {String(flags?.not_production_ready ?? true)}</span>
        <span>not_source_backed_pass = {String(flags?.not_source_backed_pass ?? true)}</span>
        <span>not_human_reviewed = {String(flags?.not_human_reviewed ?? true)}</span>
        <span>prototype_context = {String(flags?.prototype_context ?? true)}</span>
        <span>business_case_files_available = {String(flags?.business_case_files_available ?? false)}</span>
        <span>business_evidence_files_available = {String(flags?.business_evidence_files_available ?? false)}</span>
        <span>BGE-M3 = {flags?.bge_m3_status ?? "partially_effective"}</span>
        <span>full18 mode = {flags?.full18_mode ?? "mode_a_bgem3_authority_rerank"}</span>
      </div>
      <pre className="wb-json">{JSON.stringify(rules ?? {}, null, 2)}</pre>
    </section>
  );
}
