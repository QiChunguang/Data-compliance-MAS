import React from 'react';
import type { JobArtifactsResponse, RuntimeJob } from '../../types/reguthink-interactive-api';

const REVIEW_STEPS = [
  { name: '业务事实解析', desc: '识别材料范围、主体、数据类型和处理活动' },
  { name: '处理活动识别', desc: '梳理交易、共享、委托、出境等合规场景' },
  { name: '法律依据检索', desc: '从只读合规知识库检索候选依据' },
  { name: '风险项识别', desc: '形成核心风险和待补充材料清单' },
  { name: '证据与引用整理', desc: '整理证据摘要和引用说明' },
  { name: '报告草案生成', desc: '生成业务可读的审查报告' },
];

type Props = {
  job: RuntimeJob | null;
  artifacts: JobArtifactsResponse | null;
};

export const AgentClusterView: React.FC<Props> = ({ job, artifacts }) => {
  const manifest = readObject(artifacts?.['runtime_manifest.json']);
  const stages = Array.isArray(manifest.stages) ? manifest.stages as Array<{ status?: string }> : [];
  const completedCount = stages.length
    ? stages.slice(0, 6).filter((stage) => String(stage.status || '').includes('completed')).length
    : job?.status === 'completed'
      ? 6
      : 0;
  const artifactCount = job?.result_artifacts ? Object.keys(job.result_artifacts).length : artifacts ? Object.keys(artifacts).length : 0;

  return (
    <div className="agent-cluster-view">
      <div className="agent-cluster-header">
        <div>
          <p className="workspace-kicker">Compliance Review</p>
          <h2>审查与复核</h2>
          <p>6 个自动审查项 + 1 个人工复核状态。当前结果需人工复核后才能进入正式工作流。</p>
        </div>
        <div className={`workspace-job-pill ${job?.status || 'idle'}`}>
          {job?.status === 'completed' ? '审查完成' : job ? '审查处理中' : '待生成报告'}
        </div>
      </div>

      <div className="agent-cluster-summary">
        <div className="agent-summary-card">
          <div className="agent-summary-icon">6+1</div>
          <div className="agent-summary-info">
            <div className="agent-summary-value">6+1</div>
            <div className="agent-summary-label">自动审查项 + 人工复核</div>
          </div>
        </div>
        <div className="agent-summary-card">
          <div className="agent-summary-icon">✓</div>
          <div className="agent-summary-info">
            <div className="agent-summary-value">{completedCount}/6</div>
            <div className="agent-summary-label">自动审查完成</div>
          </div>
        </div>
        <div className="agent-summary-card">
          <div className="agent-summary-icon">文</div>
          <div className="agent-summary-info">
            <div className="agent-summary-value">{artifactCount}</div>
            <div className="agent-summary-label">归档材料</div>
          </div>
        </div>
        <div className="agent-summary-card">
          <div className="agent-summary-icon">人</div>
          <div className="agent-summary-info">
            <div className="agent-summary-value">未复核</div>
            <div className="agent-summary-label">人工复核状态</div>
          </div>
        </div>
      </div>

      <div className="agent-runtime-grid" data-testid="agent-cluster-automatic-agents">
        {REVIEW_STEPS.map((step, index) => (
          <div key={step.name} className={`agent-runtime-card ${index < completedCount ? 'completed' : 'pending'}`}>
            <div className="agent-card-header">
              <div className="agent-runtime-number">{String(index + 1).padStart(2, '0')}</div>
              <div className="agent-runtime-info">
                <div className="agent-runtime-name">{step.name}</div>
                <div className="agent-runtime-stage">{step.desc}</div>
              </div>
              <div className={`agent-runtime-badge ${index < completedCount ? 'completed' : 'pending'}`}>
                {index < completedCount ? '已完成' : '等待'}
              </div>
            </div>
          </div>
        ))}
        <div className="agent-runtime-card human-review-gate not_reviewed">
          <div className="agent-card-header">
            <div className="agent-runtime-number">07</div>
            <div className="agent-runtime-info">
              <div className="agent-runtime-name">人工复核</div>
              <div className="agent-runtime-stage">当前结果仅为自动审查辅助结果</div>
            </div>
            <div className="agent-runtime-badge not_reviewed">未复核</div>
          </div>
        </div>
      </div>

      <div className="agent-cluster-footer">
        <div className="agent-cluster-hint">
          <span className="hint-badge">提示</span>
          <span>生成报告后可查看自动审查项状态；正式使用前必须完成人工复核。</span>
        </div>
      </div>
    </div>
  );
};

function readObject(value: unknown): Record<string, unknown> {
  if (!value) return {};
  if (typeof value === 'string') {
    try {
      return JSON.parse(value) as Record<string, unknown>;
    } catch {
      return {};
    }
  }
  return typeof value === 'object' ? value as Record<string, unknown> : {};
}
