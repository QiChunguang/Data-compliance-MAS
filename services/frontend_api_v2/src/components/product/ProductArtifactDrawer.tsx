import React, { useState } from 'react';
import { reguthinkInteractiveClient } from '../../api/reguthinkInteractiveClient';
import type { ChatResponse, JobArtifactsResponse, RuntimeEvent, RuntimeJob } from '../../types/reguthink-interactive-api';
import { RuntimeCitationViewer } from '../runtime/RuntimeCitationViewer';
import { RuntimeEvidenceViewer } from '../runtime/RuntimeEvidenceViewer';
import { RuntimeReportViewer } from '../runtime/RuntimeReportViewer';

type ProductArtifactDrawerProps = {
  artifacts: JobArtifactsResponse | null;
  chatResponse: ChatResponse | null;
  job: RuntimeJob | null;
  events: RuntimeEvent[];
  defaultTab?: 'timeline' | 'report';
  collapsed: boolean;
  onToggle: () => void;
};

type ReviewTab = 'progress' | 'evidence' | 'review' | 'download';

const STAGE_LABELS: Record<string, string> = {
  job_created: '审查任务创建',
  queued: '等待处理',
  uploaded_materials_loaded: '材料读取',
  uploaded_material_intake_started: '材料解析',
  uploaded_material_intake_completed: '材料解析完成',
  material_parsing_started: '材料解析',
  material_parsing_completed: '材料解析完成',
  fact_extraction_started: '业务事实识别',
  fact_extraction_completed: '业务事实识别完成',
  legal_retrieval_started: '法律依据检索',
  legal_retrieval_completed: '法律依据检索完成',
  evidence_pack_started: '证据整理',
  evidence_pack_completed: '证据整理完成',
  citation_plan_started: '引用整理',
  citation_plan_completed: '引用整理完成',
  agent_analysis_started: '风险分析',
  report_generation_started: '报告草案生成',
  report_generation_completed: '报告草案生成完成',
  quality_gate_started: '复核状态确认',
  quality_gate_completed: '复核状态确认完成',
  job_completed: '审查完成',
  completed: '审查完成',
  failed: '审查失败',
};

export const ProductArtifactDrawer: React.FC<ProductArtifactDrawerProps> = ({
  artifacts,
  chatResponse,
  job,
  events,
  defaultTab = 'timeline',
  collapsed,
  onToggle,
}) => {
  const [activeTab, setActiveTab] = useState<ReviewTab>(defaultTab === 'report' ? 'download' : 'progress');
  React.useEffect(() => {
    if (job?.status === 'completed') setActiveTab('download');
    else if (job?.status === 'running' || job?.status === 'queued') setActiveTab('progress');
  }, [job?.job_id, job?.status]);

  const hasReport = !!artifacts?.['user_report.md'] || !!artifacts?.['improved_report.md'];
  const tabs: { key: ReviewTab; label: string }[] = [
    { key: 'progress', label: '审查进度' },
    { key: 'evidence', label: '证据与引用' },
    { key: 'review', label: '人工复核' },
    { key: 'download', label: '报告下载' },
  ];

  return (
    <aside className={`product-artifact-drawer ${collapsed ? 'collapsed' : ''}`}>
      <div className="product-artifact-header">
        <div className="product-artifact-header-left">
          <h3 className="product-artifact-title">
            {collapsed ? '审查' : '合规审查工作区'}
          </h3>
          {!collapsed && (
            <div className="artifact-badges">
              <span className="artifact-badge uploaded-material">6 个自动审查项</span>
              <span className="artifact-badge not-legal">人工复核：未复核</span>
            </div>
          )}
        </div>
        {!collapsed && job?.status === 'completed' && hasReport && (
          <a
            className="artifact-download-link"
            href={reguthinkInteractiveClient.artifactDownloadUrl(job.job_id, artifacts?.['user_report.md'] ? 'user_report.md' : 'improved_report.md')}
            download="user_report.md"
            data-testid="artifact-drawer-download-report"
          >
            下载报告
          </a>
        )}
        <button className="product-artifact-toggle" type="button" onClick={onToggle}>
          {collapsed ? '打开' : '收起'}
        </button>
      </div>

      {!collapsed && (
        <>
          <div className="product-artifact-tabs">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                className={`product-artifact-tab ${activeTab === tab.key ? 'active' : ''}`}
                type="button"
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="product-artifact-content">
            {activeTab === 'progress' && (
              <ReviewProgressPanel
                intake={chatResponse?.uploaded_material_intake}
                job={job}
                events={events}
              />
            )}
            {activeTab === 'evidence' && (
              <div className="report-artifact-columns">
                <RuntimeEvidenceViewer data={artifacts} />
                <RuntimeCitationViewer data={artifacts} />
              </div>
            )}
            {activeTab === 'review' && <HumanReviewPanel artifacts={artifacts} />}
            {activeTab === 'download' && <ReportDownloadPanel artifacts={artifacts} job={job} />}
          </div>
        </>
      )}
    </aside>
  );
};

function ReviewProgressPanel({
  intake,
  job,
  events,
}: {
  intake: ChatResponse['uploaded_material_intake'] | undefined;
  job: RuntimeJob | null;
  events: RuntimeEvent[];
}) {
  const stages = events.length
    ? events.slice(-10).map((event) => STAGE_LABELS[event.event_type] || STAGE_LABELS[event.stage] || '审查处理中')
    : ['等待上传材料或生成报告'];
  return (
    <div className="runtime-panel-content">
      <section className="runtime-section">
        <h4 className="runtime-section-title">审查状态</h4>
        <div className="runtime-kv">
          <span className="runtime-key">当前状态</span>
          <span className={`runtime-value runtime-status-${job?.status || 'idle'}`}>{translateStatus(job?.status)}</span>
        </div>
        <div className="runtime-kv">
          <span className="runtime-key">完成度</span>
          <span className="runtime-value">{job ? `${job.progress}%` : '0%'}</span>
        </div>
      </section>

      {intake && (
        <section className="runtime-section">
          <h4 className="runtime-section-title">材料摘要</h4>
          <div className="runtime-kv">
            <span className="runtime-key">文件数</span>
            <span className="runtime-value">{intake.file_count || 0}</span>
          </div>
          {intake.parties?.length ? (
            <div className="runtime-kv">
              <span className="runtime-key">相关主体</span>
              <span className="runtime-value">{intake.parties.join('、')}</span>
            </div>
          ) : null}
          {intake.data_type?.length ? (
            <div className="runtime-kv">
              <span className="runtime-key">数据类型</span>
              <span className="runtime-value">{intake.data_type.join('、')}</span>
            </div>
          ) : null}
        </section>
      )}

      <section className="runtime-section">
        <h4 className="runtime-section-title">审查步骤</h4>
        <div className="agent-stage-list">
          {stages.map((label, index) => (
            <div key={`${label}-${index}`} className="agent-stage-item completed">
              <span className="agent-stage-dot completed" />
              <span className="agent-stage-name">{label}</span>
              <span className="agent-stage-status completed">完成</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function HumanReviewPanel({ artifacts }: { artifacts: JobArtifactsResponse | null }) {
  const hasQuality = !!artifacts?.['quality_gate.json'];
  return (
    <section className="wb-mini-panel human-review-panel">
      <h3>人工复核</h3>
      <div className="runtime-kv">
        <span className="runtime-key">复核状态</span>
        <span className="runtime-value">未复核</span>
      </div>
      <div className="runtime-boundary-block">
        <span className="runtime-boundary-tag">非正式合规辅助分析</span>
        <span className="runtime-boundary-tag">需人工复核后使用</span>
        <span className="runtime-boundary-tag">材料仅作业务事实</span>
      </div>
      <p className="human-review-note">
        当前结果仅为自动审查辅助结果，需人工复核后才能进入正式工作流。
      </p>
      <p className="human-review-note">
        {hasQuality ? '系统已生成复核提示信息。' : '报告完成后将显示复核提示信息。'}
      </p>
    </section>
  );
}

function ReportDownloadPanel({ artifacts, job }: { artifacts: JobArtifactsResponse | null; job: RuntimeJob | null }) {
  const report = artifacts?.['user_report.md'] ?? artifacts?.['improved_report.md'];
  const artifactName = artifacts?.['user_report.md'] ? 'user_report.md' : 'improved_report.md';
  return (
    <section className="wb-mini-panel">
      <h3>报告下载</h3>
      {job?.status === 'completed' && report ? (
        <>
          <a
            className="artifact-download-link"
            href={reguthinkInteractiveClient.artifactDownloadUrl(job.job_id, artifactName)}
            download="user_report.md"
            data-testid="review-panel-download-report"
          >
            下载用户报告
          </a>
          <RuntimeReportViewer data={artifacts} />
        </>
      ) : (
        <div className="wb-placeholder">报告完成后可在此下载。</div>
      )}
    </section>
  );
}

function translateStatus(status?: string) {
  if (status === 'completed') return '已完成';
  if (status === 'failed') return '失败';
  if (status === 'running') return '生成中';
  if (status === 'queued') return '排队中';
  return '等待开始';
}
