import type { ReportResponse } from "../../types/reguthink-api";

type DiagnosticReportPanelProps = {
  report: ReportResponse | null;
  loading: boolean;
  error: string | null;
};

export function DiagnosticReportPanel({ report, loading, error }: DiagnosticReportPanelProps) {
  return (
    <section className="wb-tab-panel">
      <div className="wb-panel-heading">
        <h2>Diagnostic Report</h2>
        <span>prototype diagnostic / 不是正式法律意见</span>
      </div>
      <div className="wb-warning-line">
        本报告仅用于诊断原型展示，不构成 source-backed pass，不代表人工复核或正式法律意见。
      </div>
      {loading && <div className="wb-placeholder">loading report...</div>}
      {error && <div className="wb-error">{error}</div>}
      <pre className="wb-report-reader">{report?.improved_report_markdown ?? "missing / placeholder report"}</pre>
    </section>
  );
}
