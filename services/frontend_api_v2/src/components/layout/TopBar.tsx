import type { BaselineStatusResponse, CaseSummary, HealthResponse } from "../../types/reguthink-api";

type TopBarProps = {
  selectedCase: CaseSummary | null;
  health: HealthResponse | null;
  baseline: BaselineStatusResponse | null;
  isInteractive?: boolean;
};

export function TopBar({ selectedCase, health, baseline, isInteractive = false }: TopBarProps) {
  return (
    <header className="wb-topbar">
      <div className="wb-topbar-case">
        <span className="wb-muted">{isInteractive ? "Current conversation" : "Current case"}</span>
        <strong>{selectedCase?.case_id ?? (isInteractive ? "Interactive assessment" : "workspace welcome")}</strong>
      </div>
      <div className="wb-topbar-badges">
        <span className={health?.ok ? "wb-chip success" : "wb-chip danger"}>
          {health?.ok ? "backend connected" : "backend disconnected"}
        </span>
        <span className="wb-chip">Phase11.3 baseline</span>
        <span className="wb-chip">{baseline?.authoritative_validation_phase ?? "Phase11.2"} validation</span>
        <span className="wb-chip warning">BGE-M3 partially_effective</span>
        <span className="wb-chip warning">reranker diagnostic_only</span>
        <span className="wb-chip danger">not production-ready</span>
        <span className="wb-chip danger">not human-reviewed</span>
      </div>
    </header>
  );
}
