import type { ReactNode } from "react";
import type { BaselineStatusResponse, CaseSummary, HealthResponse } from "../../types/reguthink-api";
import { CommandBar } from "./CommandBar";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

type AppShellProps = {
  activeView: string;
  commandValue: string;
  selectedCase: CaseSummary | null;
  health: HealthResponse | null;
  baseline: BaselineStatusResponse | null;
  caseRail: ReactNode;
  children: ReactNode;
  onSelectView: (view: string) => void;
  onCommandChange: (value: string) => void;
  onCommandSubmit: () => void;
  onCommandTab: (tab: string) => void;
};

export function AppShell({
  activeView,
  commandValue,
  selectedCase,
  health,
  baseline,
  caseRail,
  children,
  onSelectView,
  onCommandChange,
  onCommandSubmit,
  onCommandTab,
}: AppShellProps) {
  return (
    <div className="wb-shell">
      <Sidebar activeView={activeView} health={health} onSelectView={onSelectView} />
      {caseRail}
      <div className="wb-main-column">
        <TopBar selectedCase={selectedCase} health={health} baseline={baseline} />
        <main className="wb-main-workspace">{children}</main>
        <CommandBar
          value={commandValue}
          runtimeEnabled={Boolean(health?.runtime_enabled)}
          onChange={onCommandChange}
          onSubmit={onCommandSubmit}
          onTab={onCommandTab}
        />
      </div>
    </div>
  );
}
