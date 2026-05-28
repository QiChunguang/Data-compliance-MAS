import React, { useMemo, useState } from 'react';
import { reguthinkInteractiveClient } from '../../api/reguthinkInteractiveClient';
import type { JobArtifactsResponse, RuntimeEvent, RuntimeJob } from '../../types/reguthink-interactive-api';
import { RuntimeReportViewer } from '../runtime/RuntimeReportViewer';
import { RuntimeEvidenceViewer } from '../runtime/RuntimeEvidenceViewer';
import { RuntimeCitationViewer } from '../runtime/RuntimeCitationViewer';

type Props = {
  conversationId: string;
  job: RuntimeJob | null;
  artifacts: JobArtifactsResponse | null;
  events: RuntimeEvent[];
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

export const ReportCenterView: React.FC<Props> = ({ conversationId, job, artifacts, events }) => {
  const [open, setOpen] = useState(true);
  const [jobs, setJobs] = useState<RuntimeJob[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [selectedArtifacts, setSelectedArtifacts] = useState<JobArtifactsResponse | null>(artifacts);
  const selectedJob = useMemo(
    () => jobs.find((item) => item.job_id === selectedJobId) ?? job,
    [jobs, selectedJobId, job],
  );
  const activeArtifacts = selectedJob?.job_id === job?.job_id ? (artifacts ?? selectedArtifacts) : selectedArtifacts;
  const manifest = useMemo(() => readObject(activeArtifacts?.['runtime_manifest.json']), [activeArtifacts]);
  const autojudge = useMemo(() => readObject(activeArtifacts?.['autojudge_result.json']), [activeArtifacts]);
  const risk = useMemo(() => readObject(activeArtifacts?.['risk_score.json']), [activeArtifacts]);
  const reportAvailable = !!activeArtifacts?.['user_report.md'] || !!activeArtifacts?.['improved_report.md'] || !!activeArtifacts?.['compliance_report.md'];
  const completed = selectedJob?.status === 'completed';
  const score = autojudge.overall_score ?? autojudge.score ?? autojudge.final_score ?? 'pending';
  const riskLevel = risk.risk_level ?? risk.overall_risk_level ?? 'pending';
  const humanReview = manifest.human_review_status ?? 'not_reviewed';

  React.useEffect(() => {
    let cancelled = false;
    async function loadJobs() {
      if (!conversationId) {
        setJobs(job ? [job] : []);
        setSelectedJobId(job?.job_id || '');
        return;
      }
      const loaded = await reguthinkInteractiveClient.listConversationJobs(conversationId);
      if (cancelled) return;
      const completedJobs = loaded.filter((item) => item.status === 'completed');
      setJobs(completedJobs.length ? completedJobs : loaded);
      const firstId = completedJobs[0]?.job_id || loaded[0]?.job_id || job?.job_id || '';
      setSelectedJobId((current) => current || firstId);
    }
    void loadJobs().catch(() => {
      if (!cancelled) {
        setJobs(job ? [job] : []);
        setSelectedJobId(job?.job_id || '');
      }
    });
    return () => { cancelled = true; };
  }, [conversationId, job?.job_id]);

  React.useEffect(() => {
    let cancelled = false;
    async function loadArtifacts() {
      if (!selectedJob?.job_id) {
        setSelectedArtifacts(null);
        return;
      }
      if (selectedJob.job_id === job?.job_id && artifacts) {
        setSelectedArtifacts(artifacts);
        return;
      }
      const loadedArtifacts = await reguthinkInteractiveClient.getJobArtifacts(selectedJob.job_id);
      if (!cancelled) setSelectedArtifacts(loadedArtifacts);
    }
    void loadArtifacts().catch(() => {
      if (!cancelled) setSelectedArtifacts(null);
    });
    return () => { cancelled = true; };
  }, [selectedJob?.job_id, job?.job_id, artifacts]);

  return (
    <section className="workspace-page product-report-center" data-testid="report-center-view">
      <div className="workspace-hero">
        <div>
          <p className="workspace-kicker">Review Reports</p>
          <h2>报告中心</h2>
          <p>展示当前会话下已生成的审查报告，可查看历史版本并下载用户报告。</p>
        </div>
        <div className={`workspace-job-pill ${selectedJob?.status || 'idle'}`}>
          {selectedJob ? translateStatus(selectedJob.status) : '暂无报告'}
        </div>
      </div>

      {!selectedJob && (
        <div className="workspace-panel report-empty-state">
          <h3>暂无报告</h3>
          <p>上传业务材料并点击「生成审查报告」后，这里会显示报告历史。</p>
        </div>
      )}

      {selectedJob && (
        <div className="report-center-grid">
          <div className="report-job-list" data-testid="report-center-job-history">
            {jobs.map((item) => (
              <button
                key={item.job_id}
                className={`report-job-card ${selectedJob.job_id === item.job_id ? 'active' : ''}`}
                type="button"
                onClick={() => { setSelectedJobId(item.job_id); setOpen(true); }}
              >
                <span className="report-card-kicker">审查报告</span>
                <strong>{`报告 ${jobs.length - jobs.findIndex((j) => j.job_id === item.job_id)}`}</strong>
                <span>{labelAssessment(item.assessment_type)}</span>
                <span>{new Date(item.created_at).toLocaleString()}</span>
                <div className="report-card-metrics">
                  <span>{translateStatus(item.status)}</span>
                  <span>{item.job_id === selectedJob.job_id && reportAvailable ? '可下载' : item.result_artifacts?.['user_report.md'] || item.result_artifacts?.['improved_report.md'] ? '可下载' : '生成中'}</span>
                </div>
              </button>
            ))}
          </div>

          <aside className="report-center-side">
            <h3>边界状态</h3>
            <span className="report-boundary-chip">非正式法律意见</span>
            <span className="report-boundary-chip">未人工复核</span>
            <span className="report-boundary-chip">上传材料仅为业务事实</span>
            <span className="report-boundary-chip">法律依据来自只读合规知识库</span>
            <div className="workspace-kv"><span>进度记录</span><strong>{events.length}</strong></div>
            <div className="workspace-kv"><span>归档材料</span><strong>{activeArtifacts ? Object.keys(activeArtifacts).length : 0}</strong></div>
            {completed && reportAvailable && (
              <a
                className="report-download-link"
                href={reguthinkInteractiveClient.artifactDownloadUrl(selectedJob.job_id, activeArtifacts?.['user_report.md'] ? 'user_report.md' : 'improved_report.md')}
                download="user_report.md"
                data-testid="report-center-download-report"
              >
                下载用户报告
              </a>
            )}
          </aside>
        </div>
      )}

      {selectedJob && open && (
        <div className="report-center-detail" data-testid="report-center-artifacts">
          {!completed && (
            <div className="workspace-panel">
              <h3>报告尚未完成</h3>
              <p>当前阶段：{selectedJob.current_stage}，进度：{selectedJob.progress}%。</p>
            </div>
          )}
          {completed && activeArtifacts && (
            <>
              <RuntimeReportViewer data={activeArtifacts} />
              <div className="report-artifact-columns">
                <RuntimeEvidenceViewer data={activeArtifacts} />
                <RuntimeCitationViewer data={activeArtifacts} />
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
};

function translateStatus(status?: string) {
  if (status === 'completed') return '已完成';
  if (status === 'failed') return '失败';
  if (status === 'running') return '生成中';
  if (status === 'queued') return '排队中';
  return '等待开始';
}

function labelAssessment(value?: string) {
  if (value === 'cross_border_data_transfer') return '跨境数据传输审查';
  if (value === 'data_transaction_compliance') return '数据交易合规审查';
  return '数据合规审查';
}
