import type { JobArtifactsResponse } from '../../types/reguthink-interactive-api';

export function RuntimeCitationViewer({ data }: { data: unknown }) {
  const artifacts = data && typeof data === 'object' ? data as JobArtifactsResponse : {};
  const raw = artifacts['citation_plan.json'];
  let citations: Array<Record<string, unknown>> = [];
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
    citations = (parsed?.citations || parsed?.items || []) as Array<Record<string, unknown>>;
  } catch {
    citations = [];
  }
  return (
    <section className="wb-mini-panel">
      <h3>引用说明</h3>
      {citations.length ? (
        <div className="agent-stage-list">
          {citations.slice(0, 8).map((item, index) => (
            <div key={index} className="agent-stage-item completed">
              <span className="agent-stage-dot completed" />
              <span className="agent-stage-name">
                {String(item.law_reference || item.source_title || item.title || item.content || '引用条目').slice(0, 140)}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="wb-placeholder">暂无引用摘要。</div>
      )}
    </section>
  );
}
