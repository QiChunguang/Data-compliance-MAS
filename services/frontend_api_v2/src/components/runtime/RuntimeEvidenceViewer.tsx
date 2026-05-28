import type { JobArtifactsResponse } from '../../types/reguthink-interactive-api';

function extractEvidence(data: unknown): unknown {
  if (!data || typeof data !== 'object') return { state: 'missing' };
  const artifacts = data as JobArtifactsResponse;
  const raw = artifacts['evidence_pack.json'];
  if (!raw) return { state: 'evidence_pack.json not found' };
  try {
    return typeof raw === 'string' ? JSON.parse(raw) : raw;
  } catch {
    return String(raw);
  }
}

export function RuntimeEvidenceViewer({ data }: { data: unknown }) {
  const evidence = extractEvidence(data);
  const ev = evidence as Record<string, unknown> | null;
  const rows = (ev?.evidence_rows || ev?.evidence_items || []) as Array<string | Record<string, unknown>>;

  return (
    <section className="wb-mini-panel">
      <h3>证据整理</h3>
      <div className="wb-warning-line">证据摘要用于辅助审查，不代表人工复核完成。</div>
      {rows && rows.length > 0 && (
        <div style={{ marginTop: 'var(--space-md)' }}>
          <h4 style={{ fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)', marginBottom: 'var(--space-sm)' }}>
            证据条目 ({rows.length})
          </h4>
          <div className="agent-stage-list">
            {rows.map((row, i) => (
              <div key={i} className="agent-stage-item">
                <span className="agent-stage-dot completed" />
                <span className="agent-stage-name">{summarizeEvidence(row)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {(!ev && !rows) && (
        <div className="wb-placeholder">暂无证据摘要。</div>
      )}
    </section>
  );
}

function summarizeEvidence(row: string | Record<string, unknown>): string {
  const text = typeof row === 'string'
    ? row
    : String(row.source_title || row.title || row.content || row.snippet || row.evidence_text || '证据条目');
  return text.length > 120 ? `${text.slice(0, 120)}...` : text;
}
