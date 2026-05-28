import React from 'react';
import type { JobArtifactsResponse } from '../../types/reguthink-interactive-api';

const DEFAULT_RISK_CATEGORIES = [
  {
    name: '数据交易风险',
    level: 'medium',
    items: ['交易主体资质', '数据确权', '定价机制', '合同条款'],
    score: 65,
  },
  {
    name: '跨境传输风险',
    level: 'high',
    items: ['出境安全评估', '标准合同', '认证机制', '监管审批'],
    score: 78,
  },
  {
    name: '个人信息保护风险',
    level: 'high',
    items: ['告知同意', '最小必要', '敏感信息', '跨境提供'],
    score: 82,
  },
  {
    name: '数据流通安全风险',
    level: 'medium',
    items: ['访问控制', '加密传输', '日志审计', '应急响应'],
    score: 58,
  },
  {
    name: '证据缺口风险',
    level: 'low',
    items: ['证据完整性', '人工核验', '条文核查', '复核记录'],
    score: 35,
  },
  {
    name: '来源核查风险',
    level: 'medium',
    items: ['溯源完整性', '引用准确性', '版本一致性', '更新时效'],
    score: 52,
  },
];

type RiskItem = {
  name: string;
  level: string;
  items: string[];
  score: number;
};

type Props = {
  artifacts: JobArtifactsResponse | null;
};

function parseRiskData(artifacts: JobArtifactsResponse | null): {
  categories: RiskItem[];
  overall: string | null;
  confidence: string | null;
  isReal: boolean;
  scoreBreakdown: Record<string, number> | null;
  qualityGate: string | null;
} {
  if (!artifacts) return { categories: DEFAULT_RISK_CATEGORIES, overall: null, confidence: null, isReal: false, scoreBreakdown: null, qualityGate: null };

  const riskRaw = artifacts['risk_score.json'];
  if (!riskRaw) return { categories: DEFAULT_RISK_CATEGORIES, overall: null, confidence: null, isReal: false, scoreBreakdown: null, qualityGate: null };

  try {
    const risk =
      typeof riskRaw === 'string' ? JSON.parse(riskRaw) : (riskRaw as Record<string, unknown>);

    const categories: RiskItem[] = [];
    const dims: Record<string, string> = {
      transaction_risk: '数据交易风险',
      personal_information_risk: '个人信息保护风险',
      sensitive_pi_risk: '敏感PI风险',
      cross_border_risk: '跨境传输风险',
      evidence_gap_risk: '证据缺口风险',
      source_trace_risk: '来源核查风险',
    };

    for (const [key, label] of Object.entries(dims)) {
      const dim = risk[key] as Record<string, unknown> | undefined;
      if (dim) {
        categories.push({
          name: label,
          level: (dim.level as string) || 'medium',
          items: [],
          score: (dim.score as number) || 0,
        });
      }
    }

    const scoreBreakdown = risk.score_breakdown as Record<string, number> | undefined || null;
    const qualityGate = risk.quality_gate as string | undefined || null;

    return {
      categories: categories.length > 0 ? categories : DEFAULT_RISK_CATEGORIES,
      overall: (risk.overall_risk_level as string) || null,
      confidence: (risk.confidence as string) || null,
      isReal: categories.length > 0,
      scoreBreakdown,
      qualityGate,
    };
  } catch {
    return { categories: DEFAULT_RISK_CATEGORIES, overall: null, confidence: null, isReal: false, scoreBreakdown: null, qualityGate: null };
  }
}

export const RiskRadarView: React.FC<Props> = ({ artifacts }) => {
  const { categories, overall, confidence, isReal, scoreBreakdown, qualityGate } = parseRiskData(artifacts);
  const maxScore = Math.max(...categories.map((r) => r.score), 100);
  const avgScore = categories.length > 0
    ? Math.round(categories.reduce((sum, r) => sum + r.score, 0) / categories.length)
    : 0;

  const overallText = overall === 'critical' ? '严重' : overall === 'high' ? '高风险' : overall === 'medium' ? '中风险' : overall === 'low' ? '低风险' : '未评估';

  return (
    <div className="risk-radar-view">
      <div className="risk-header">
        <div>
          <p className="workspace-kicker">Risk Review</p>
          <h2>风险雷达</h2>
          <p>
            {isReal
              ? `基于上传材料的风险评估 — 综合等级: ${overallText}`
              : '数据合规多维度风险评估仪表盘'}
          </p>
        </div>
        <div className={`workspace-job-pill ${overall || 'unknown'}`}>
          {isReal ? overallText : '模拟数据'}
        </div>
      </div>

      <div className="risk-dashboard">
        {/* Overview Bar */}
        <div className="risk-overview-bar">
          <div className="risk-overview-card">
            <div className="risk-overview-label">综合风险等级</div>
            <div className={`risk-overview-value ${overall || 'low'}`}>{overallText}</div>
            <div className="risk-overview-sub">{isReal ? '基于真实评估' : '模拟评估'}</div>
          </div>
          <div className="risk-overview-card">
            <div className="risk-overview-label">平均风险评分</div>
            <div className={`risk-overview-value ${avgScore >= 70 ? 'high' : avgScore >= 40 ? 'medium' : 'low'}`}>{avgScore}</div>
            <div className="risk-overview-sub">满分 100</div>
          </div>
          <div className="risk-overview-card">
            <div className="risk-overview-label">评估维度</div>
            <div className="risk-overview-value">{categories.length}</div>
            <div className="risk-overview-sub">风险分类</div>
          </div>
          {qualityGate && (
            <div className="risk-overview-card">
              <div className="risk-overview-label">质量门</div>
              <div className={`risk-overview-value ${qualityGate === 'passed' ? 'low' : 'high'}`}>{qualityGate}</div>
              <div className="risk-overview-sub">审查质量</div>
            </div>
          )}
          {confidence && (
            <div className="risk-overview-card">
              <div className="risk-overview-label">置信度</div>
              <div className="risk-overview-value">{confidence}</div>
              <div className="risk-overview-sub">可信度提示</div>
            </div>
          )}
        </div>

        {/* Main Grid */}
        <div className="risk-main-grid">
          {/* Left: Category List */}
          <div className="risk-category-panel">
            <h3 className="risk-panel-title">分类风险概览</h3>
            <div className="risk-category-list">
              {categories.map((risk) => (
                <div key={risk.name} className="risk-category-item">
                  <div className="risk-category-header">
                    <span className="risk-category-name">{risk.name}</span>
                    <span className={`risk-category-badge ${risk.level}`}>
                      {risk.level === 'critical'
                        ? '严重'
                        : risk.level === 'high'
                          ? '高风险'
                          : risk.level === 'medium'
                            ? '中风险'
                            : '低风险'}
                    </span>
                  </div>
                  <div className="risk-category-track">
                    <div
                      className={`risk-category-fill ${risk.level}`}
                      style={{ width: `${Math.min((risk.score / maxScore) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="risk-category-score">
                    <span>评分: {risk.score}</span>
                    <span>{Math.round((risk.score / maxScore) * 100)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Detail Panel */}
          <div className="risk-detail-panel">
            <div className="risk-detail-section">
              <h4>风险说明</h4>
              <p className="risk-detail-text">
                {isReal
                  ? '以上为基于上传材料的规则型风险提示。评分基于事实抽取、法规匹配和合规分析自动生成，仅供参考，不构成法律意见。'
                  : '当前为示例风险视图，不代表真实合规评价。正式使用需生成报告并完成人工复核。'}
              </p>
            </div>

            {scoreBreakdown && (
              <div className="risk-detail-section">
                <h4>评分细项</h4>
                <div className="risk-detail-tags">
                  {Object.entries(scoreBreakdown).map(([key, value]) => (
                    <span key={key} className="risk-detail-tag">
                      {key}: {typeof value === 'number' ? value.toFixed(1) : String(value)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="risk-detail-section">
              <h4>建议措施</h4>
              <p className="risk-detail-text">
                1. 完善数据交易合同条款，明确数据权属和定价机制。<br />
                2. 对跨境数据传输进行安全评估，确保符合出境要求。<br />
                3. 建立个人信息保护制度，落实告知同意和最小必要原则。<br />
                4. 补充证据链和引用依据，提高评估可信度。
              </p>
            </div>

            <div className="risk-detail-section">
              <h4>证据缺口</h4>
              <div className="risk-detail-tags">
                <span className="risk-detail-tag">证据完整性说明</span>
                <span className="risk-detail-tag">人工核验记录</span>
                <span className="risk-detail-tag">条文核查记录</span>
                <span className="risk-detail-tag">复核记录</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="risk-footer">
        <div className="risk-hint">
          <span className="hint-badge">提示</span>
          {isReal ? (
            <span>以上为基于上传材料的规则型风险提示。不是正式评分，不构成法律意见。</span>
          ) : (
            <span>当前为示例风险视图，不代表真实合规评价。正式使用需生成报告并完成人工复核。</span>
          )}
        </div>
      </div>
    </div>
  );
};
