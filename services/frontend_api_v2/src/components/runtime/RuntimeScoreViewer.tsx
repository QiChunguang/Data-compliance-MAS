import type { JobArtifactsResponse } from '../../types/reguthink-interactive-api';

function extractRiskScore(data: unknown): unknown {
  if (!data || typeof data !== 'object') return { state: 'missing' };
  const artifacts = data as JobArtifactsResponse;
  const riskRaw = artifacts['risk_score.json'];
  if (!riskRaw) return { state: 'risk_score.json not found' };
  try {
    return typeof riskRaw === 'string' ? JSON.parse(riskRaw) : riskRaw;
  } catch {
    return String(riskRaw);
  }
}

export function RuntimeScoreViewer({ data }: { data: unknown }) {
  const riskData = extractRiskScore(data);

  const risk = riskData as Record<string, unknown> | null;
  const overall = risk?.overall_risk_level as string | undefined;
  const confidence = risk?.confidence as string | undefined;
  const dims = risk && typeof risk === 'object'
    ? Object.entries(risk).filter(([k]) =>
        k.endsWith('_risk') && typeof risk[k] === 'object')
    : [];

  return (
    <section className="wb-mini-panel">
      <h3>风险评分</h3>
      <div className="wb-warning-line">规则型风险评分，不是 AutoJudge 正式评分，不构成法律意见。</div>

      {overall && (
        <div className={`risk-overall-badge ${overall}`}>
          综合风险: {overall === 'critical' ? '严重' : overall === 'high' ? '高风险' : overall === 'medium' ? '中风险' : '低风险'}
        </div>
      )}
      {confidence && <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', marginTop: 'var(--space-xs)' }}>置信度: {confidence}</div>}

      {dims.length > 0 && (
        <div style={{ display: 'grid', gap: 'var(--space-sm)', marginTop: 'var(--space-md)' }}>
          {dims.map(([key, val]) => {
            const dim = val as Record<string, unknown>;
            const level = dim.level as string || 'unknown';
            const score = dim.score as number || 0;
            return (
              <div key={key} style={{ padding: 'var(--space-sm)', border: '1px solid var(--border-soft)', borderRadius: 'var(--radius-md)', background: 'var(--bg-input)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-xs)' }}>
                  <span style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: 'var(--text-primary)' }}>{key}</span>
                  <span style={{ fontSize: 'var(--text-sm)', color: level === 'critical' ? 'var(--danger)' : level === 'high' ? 'var(--warning)' : 'var(--text-secondary)' }}>
                    {level} ({score})
                  </span>
                </div>
                <div style={{ height: 4, borderRadius: 'var(--radius-full)', background: 'var(--bg-hover)', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${Math.min(score, 100)}%`, borderRadius: 'var(--radius-full)',
                    background: level === 'critical' ? 'var(--danger)' : level === 'high' ? 'var(--warning)' : level === 'medium' ? 'var(--accent)' : 'var(--success)'
                  }} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {(!overall && dims.length === 0) && (
        <pre className="wb-json">{JSON.stringify(data ?? { state: 'missing' }, null, 2)}</pre>
      )}
    </section>
  );
}