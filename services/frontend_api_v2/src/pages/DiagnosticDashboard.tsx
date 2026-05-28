import { useEffect, useMemo, useState } from "react";
import { ReguThinkClientError, reguthinkClient } from "../api/reguthinkClient";
import { CaseRail, type CaseFilter } from "../components/cases/CaseRail";
import { AppShell } from "../components/layout/AppShell";
import { DiagnosticWorkspace } from "../components/workspace/DiagnosticWorkspace";
import type {
  BaselineStatusResponse,
  CaseArtifactsResponse,
  CaseSummary,
  HealthResponse,
  ReportResponse,
} from "../types/reguthink-api";

type LoadState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

function emptyState<T>(): LoadState<T> {
  return { data: null, loading: true, error: null };
}

function errorMessage(error: unknown): string {
  if (error instanceof ReguThinkClientError) {
    return `${error.kind}: ${error.message}`;
  }
  return error instanceof Error ? error.message : "Unknown error";
}

const VIEW_TO_TAB: Record<string, string> = {
  workbench: "overview",
  matrix: "overview",
  report: "report",
  evidence: "evidence",
  citations: "citations",
  score: "score",
  rag: "rag",
  boundaries: "boundaries",
};

type Props = {
  activeView: string;
  onSelectView: (view: string) => void;
};

export function DiagnosticDashboard({ activeView, onSelectView }: Props) {
  const [health, setHealth] = useState<LoadState<HealthResponse>>(emptyState());
  const [baseline, setBaseline] = useState<LoadState<BaselineStatusResponse>>(emptyState());
  const [cases, setCases] = useState<LoadState<CaseSummary[]>>(emptyState());
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const [caseQuery, setCaseQuery] = useState("");
  const [commandValue, setCommandValue] = useState("");
  const [caseFilter, setCaseFilter] = useState<CaseFilter>("all");
  const [activeTab, setActiveTab] = useState("overview");
  const [caseDetail, setCaseDetail] = useState<LoadState<CaseSummary>>({ data: null, loading: false, error: null });
  const [artifacts, setArtifacts] = useState<LoadState<CaseArtifactsResponse>>({
    data: null,
    loading: false,
    error: null,
  });
  const [report, setReport] = useState<LoadState<ReportResponse>>({ data: null, loading: false, error: null });

  useEffect(() => {
    async function loadInitial() {
      try {
        const [healthData, baselineData, caseList] = await Promise.all([
          reguthinkClient.getHealth(),
          reguthinkClient.getBaselineStatus(),
          reguthinkClient.getCases(),
        ]);
        setHealth({ data: healthData, loading: false, error: null });
        setBaseline({ data: baselineData, loading: false, error: null });
        setCases({ data: caseList.cases, loading: false, error: null });
        setSelectedCaseId(caseList.cases[0]?.case_id ?? "");
      } catch (error) {
        const message = errorMessage(error);
        setHealth((current) => ({ ...current, loading: false, error: message }));
        setBaseline((current) => ({ ...current, loading: false, error: message }));
        setCases((current) => ({ ...current, loading: false, error: message }));
      }
    }

    void loadInitial();
  }, []);

  useEffect(() => {
    if (!selectedCaseId) {
      return;
    }

    setCaseDetail({ data: null, loading: true, error: null });
    setArtifacts({ data: null, loading: true, error: null });
    setReport({ data: null, loading: true, error: null });

    async function loadSelectedCase() {
      try {
        const [detailData, artifactData, reportData] = await Promise.all([
          reguthinkClient.getCase(selectedCaseId),
          reguthinkClient.getCaseArtifacts(selectedCaseId),
          reguthinkClient.getCaseReport(selectedCaseId),
        ]);
        setCaseDetail({ data: detailData, loading: false, error: null });
        setArtifacts({ data: artifactData, loading: false, error: null });
        setReport({ data: reportData, loading: false, error: null });
      } catch (error) {
        const message = errorMessage(error);
        setCaseDetail((current) => ({ ...current, loading: false, error: message }));
        setArtifacts((current) => ({ ...current, loading: false, error: message }));
        setReport((current) => ({ ...current, loading: false, error: message }));
      }
    }

    void loadSelectedCase();
  }, [selectedCaseId]);

  const selectedCase = useMemo(
    () => cases.data?.find((item) => item.case_id === selectedCaseId) ?? caseDetail.data,
    [caseDetail.data, cases.data, selectedCaseId],
  );

  function selectViewInternal(view: string) {
    onSelectView(view);
    setActiveTab(VIEW_TO_TAB[view] ?? "overview");
  }

  function submitCommand() {
    setCaseQuery(commandValue);
  }

  function selectWelcomeTab(tab: string) {
    onSelectView(tab === "overview" ? "matrix" : tab);
    setActiveTab(tab);
    if (tab === "score") {
      setCaseFilter("lt70");
    }
  }

  return (
    <AppShell
      activeView={activeView}
      commandValue={commandValue}
      selectedCase={selectedCase}
      health={health.data}
      baseline={baseline.data}
      onSelectView={selectViewInternal}
      onCommandChange={setCommandValue}
      onCommandSubmit={submitCommand}
      onCommandTab={(tab) => {
        setActiveTab(tab);
        onSelectView(tab);
      }}
      caseRail={
        <CaseRail
          cases={cases.data ?? []}
          selectedCaseId={selectedCaseId}
          query={caseQuery}
          filter={caseFilter}
          onQueryChange={setCaseQuery}
          onFilterChange={setCaseFilter}
          onSelectCase={setSelectedCaseId}
        />
      }
    >
      {(health.error || baseline.error || cases.error) && (
        <div className="wb-error wb-top-error">{health.error ?? baseline.error ?? cases.error}</div>
      )}
      <DiagnosticWorkspace
        selectedCase={selectedCase}
        artifacts={artifacts.data}
        report={report.data}
        health={health.data}
        baseline={baseline.data}
        activeTab={activeTab}
        reportLoading={report.loading}
        reportError={report.error}
        onTabChange={setActiveTab}
        onWelcomeAction={selectWelcomeTab}
      />
    </AppShell>
  );
}
