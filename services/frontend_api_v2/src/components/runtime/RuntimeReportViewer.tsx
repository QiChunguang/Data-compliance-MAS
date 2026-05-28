import type { JobArtifactsResponse } from '../../types/reguthink-interactive-api';

function extractReport(data: unknown): string | null {
  if (!data || typeof data !== 'object') return null;
  const artifacts = data as JobArtifactsResponse;
  const reportRaw = artifacts['user_report.md'] ?? artifacts['improved_report.md'] ?? artifacts['compliance_report.md'];
  if (!reportRaw) return null;
  return typeof reportRaw === 'string' ? reportRaw : String(reportRaw);
}

export function RuntimeReportViewer({ data }: { data: unknown }) {
  const report = extractReport(data);

  return (
    <section className="wb-mini-panel">
      <h3>审查报告</h3>
      <div className="wb-warning-line">本报告为非正式合规辅助分析，需人工复核后使用。</div>
      {report ? (
        <pre className="wb-report-reader">{report}</pre>
      ) : (
        <pre className="wb-report-reader">报告尚未生成。</pre>
      )}
    </section>
  );
}
