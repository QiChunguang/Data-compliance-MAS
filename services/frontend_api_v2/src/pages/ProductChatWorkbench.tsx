import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { reguthinkClient } from '../api/reguthinkClient';
import { ReguThinkInteractiveError, reguthinkInteractiveClient } from '../api/reguthinkInteractiveClient';
import { ProductSidebar } from '../components/product/ProductSidebar';
import { ProductConversationRail } from '../components/product/ProductConversationRail';
import { ProductChatWorkspace } from '../components/product/ProductChatWorkspace';
import { ProductChatComposer, type ReportTriggerStatus } from '../components/product/ProductChatComposer';
import { ProductArtifactDrawer } from '../components/product/ProductArtifactDrawer';
import { AgentClusterView } from '../components/product/AgentClusterView';
import { KnowledgeGraphView } from '../components/product/KnowledgeGraphView';
import { RiskRadarView } from '../components/product/RiskRadarView';
import { DataImportView } from '../components/product/DataImportView';
import { ReportCenterView } from '../components/product/ReportCenterView';
import type { BaselineStatusResponse, HealthResponse } from '../types/reguthink-api';
import type {
  AssessmentType,
  AssessmentTypeInfo,
  ChatResponse,
  Conversation,
  JobArtifactsResponse,
  Message,
  RuntimeEvent,
  RuntimeJob,
  UploadedFile,
} from '../types/reguthink-interactive-api';

const DEFAULT_ASSESSMENT: AssessmentType = 'data_transaction_compliance';

const CROSS_BORDER_KEYWORDS = [
  '出境', '跨境', '境外', 'overseas', 'foreign recipient',
  '境外接收方', '数据出海', '跨国传输', '新加坡', '海外',
  'cross-border', 'cross border', 'foreign',
];

type Props = {
  activeView: string;
  onSelectView: (view: string) => void;
};

function mergeMessages(existing: Message[], incoming: Message[]): Message[] {
  const map = new Map<string, Message>();
  for (const m of existing) map.set(m.message_id, m);
  for (const m of incoming) map.set(m.message_id, m);
  return Array.from(map.values()).sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );
}

export function ProductChatWorkbench({ activeView, onSelectView }: Props) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [baseline, setBaseline] = useState<BaselineStatusResponse | null>(null);
  const [assessmentTypes, setAssessmentTypes] = useState<AssessmentTypeInfo[]>([]);
  const [assessmentType, setAssessmentType] = useState<AssessmentType>(DEFAULT_ASSESSMENT);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [events, setEvents] = useState<RuntimeEvent[]>([]);
  const [job, setJob] = useState<RuntimeJob | null>(null);
  const [artifacts, setArtifacts] = useState<JobArtifactsResponse | null>(null);
  const [composerValue, setComposerValue] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAllConversations, setShowAllConversations] = useState(false);
  const [artifactDrawerCollapsed, setArtifactDrawerCollapsed] = useState(true);
  const [artifactDefaultTab, setArtifactDefaultTab] = useState<'timeline' | 'report'>('timeline');
  const [lastChatResponse, setLastChatResponse] = useState<ChatResponse | null>(null);
  const [showCrossBorderPrompt, setShowCrossBorderPrompt] = useState(false);
  const [reportStatus, setReportStatus] = useState<ReportTriggerStatus>('idle');
  const [reportJobId, setReportJobId] = useState<string | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const isSendingRef = useRef(false);
  const conversationTokenRef = useRef(0);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);

  const selectedConversation = useMemo(
    () => conversations.find((item) => item.conversation_id === selectedConversationId) ?? null,
    [conversations, selectedConversationId]
  );

  async function refreshConversations() {
    const list = await reguthinkInteractiveClient.listConversations();
    const sorted = [...list].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    );
    setConversations(sorted);
    return sorted;
  }

  const loadConversation = useCallback(async (conversationId: string, token: number) => {
    if (!conversationId) return;
    const [messageList, fileList, latestJob] = await Promise.all([
      reguthinkInteractiveClient.getMessages(conversationId),
      reguthinkInteractiveClient.listFiles(conversationId),
      reguthinkInteractiveClient.getLatestJob(conversationId),
    ]);
    if (token !== conversationTokenRef.current) return;
    setMessages(messageList);
    setFiles(fileList);
      setJob(latestJob);
      setReportJobId(latestJob?.job_id || null);
      setReportStatus(latestJob?.status === 'completed' ? 'completed' : latestJob?.status === 'failed' ? 'failed' : latestJob ? 'running' : 'idle');
      if (latestJob?.job_id) {
      const [eventLog, loadedArtifacts] = await Promise.all([
        reguthinkInteractiveClient.getJobEvents(latestJob.job_id),
        reguthinkInteractiveClient.getJobArtifacts(latestJob.job_id),
      ]);
      if (token !== conversationTokenRef.current) return;
      setEvents(eventLog.events);
      setArtifacts(loadedArtifacts);
      setArtifactDrawerCollapsed(false);
    } else {
      setEvents([]);
      setArtifacts(null);
      setArtifactDrawerCollapsed(true);
    }
  }, []);

  useEffect(() => {
    async function boot() {
      try {
        const [healthData, baselineData, typeList, conversationList] = await Promise.all([
          reguthinkClient.getHealth(),
          reguthinkClient.getBaselineStatus(),
          reguthinkInteractiveClient.getAssessmentTypes(),
          reguthinkInteractiveClient.listConversations(),
        ]);
        setHealth(healthData);
        setBaseline(baselineData);
        setAssessmentTypes(typeList);
        setConversations([...conversationList].sort(
          (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        ));
        setSelectedConversationId('');
      } catch (err) {
        setError(readableError(err));
      } finally {
        setLoading(false);
      }
    }
    void boot();
  }, []);

  useEffect(() => {
    if (isSendingRef.current) {
      return;
    }
    if (selectedConversationId) {
      conversationTokenRef.current += 1;
      const token = conversationTokenRef.current;
      setEvents([]);
      setJob(null);
      setArtifacts(null);
      setLastChatResponse(null);
      setArtifactDrawerCollapsed(true);
      void loadConversation(selectedConversationId, token).catch((err) =>
        setError(readableError(err))
      );
    } else {
      setMessages([]);
      setFiles([]);
      setEvents([]);
      setJob(null);
      setArtifacts(null);
      setLastChatResponse(null);
      setReportStatus('idle');
      setReportJobId(null);
      setReportError(null);
    }
  }, [selectedConversationId, loadConversation]);

  function readableError(err: unknown): string {
    return err instanceof ReguThinkInteractiveError
      ? `${err.kind}: ${err.message}`
      : err instanceof Error
      ? err.message
      : 'Unknown error';
  }

  async function createConversation(type?: AssessmentType): Promise<string | undefined> {
    setBusy(true);
    setError(null);
    try {
      conversationTokenRef.current += 1;
      const conversation = await reguthinkInteractiveClient.createConversation({
        title: `交互式诊断 ${new Date().toLocaleTimeString()}`,
        assessment_type: type ?? assessmentType,
      });
      if (type) setAssessmentType(type);
      setConversations((current) => [
        conversation,
        ...current.filter((item) => item.conversation_id !== conversation.conversation_id),
      ]);
      setMessages([]);
      setFiles([]);
      setEvents([]);
      setJob(null);
      setArtifacts(null);
      setLastChatResponse(null);
      setComposerValue('');
      setReportStatus('idle');
      setReportJobId(null);
      setReportError(null);
      setArtifactDrawerCollapsed(true);
      setSelectedConversationId(conversation.conversation_id);
      window.setTimeout(() => composerRef.current?.focus(), 0);
      return conversation.conversation_id;
    } catch (err) {
      setError(readableError(err));
      return undefined;
    } finally {
      setBusy(false);
    }
  }

  async function sendMessage() {
    if (!composerValue.trim()) return;
    setBusy(true);
    setError(null);
    isSendingRef.current = true;
    try {
      let convId = selectedConversationId;
      if (!convId) {
        const conversation = await reguthinkInteractiveClient.createConversation({
          title: `交互式诊断 ${new Date().toLocaleTimeString()}`,
          assessment_type: assessmentType,
        });
        convId = conversation.conversation_id;
        conversationTokenRef.current += 1;
        setSelectedConversationId(convId);
      }
      const token = conversationTokenRef.current;
      const prompt = composerValue.trim();
      const response = await reguthinkInteractiveClient.chat(convId, {
        content: prompt,
        message: prompt,
        assessment_type: assessmentType,
        file_ids: files.map((f) => f.file_id),
        auto_run_assessment: false,
        runtime_mode: 'chat',
        action: 'send_message',
        rag_enabled: true,
        autojudge_enabled: false,
      });
      if (token !== conversationTokenRef.current) return;
      setComposerValue('');
      setLastChatResponse(response);
      setMessages((prev) => mergeMessages(prev, [response.user_message, response.assistant_message]));
      setArtifactDrawerCollapsed(true);
      await refreshConversations();
    } catch (err) {
      setError(readableError(err));
    } finally {
      isSendingRef.current = false;
      setBusy(false);
    }
  }

  async function uploadFile(file: File, targetConversationId?: string): Promise<string | undefined> {
    setBusy(true);
    setError(null);
    isSendingRef.current = true;
    try {
      let convId = targetConversationId || selectedConversationId;
      if (!convId) {
        const conversation = await reguthinkInteractiveClient.createConversation({
          title: `交互式诊断 ${new Date().toLocaleTimeString()}`,
          assessment_type: assessmentType,
        });
        convId = conversation.conversation_id;
        conversationTokenRef.current += 1;
        setSelectedConversationId(convId);
        await refreshConversations();
      }
      await reguthinkInteractiveClient.uploadFile(convId, file);
      const token = conversationTokenRef.current;
      await loadConversation(convId, token);
      await refreshConversations();
      return convId;
    } catch (err) {
      setError(readableError(err));
      return undefined;
    } finally {
      isSendingRef.current = false;
      setBusy(false);
    }
  }

  function removeFileFromCurrentContext(fileId: string) {
    setFiles((current) => current.filter((file) => file.file_id !== fileId));
  }

  function createLocalAssistantMessage(content: string, metadata: Record<string, unknown> = {}): Message {
    return {
      message_id: `local_${Date.now()}_${Math.random().toString(16).slice(2)}`,
      conversation_id: selectedConversationId || 'local',
      role: 'assistant',
      content,
      created_at: new Date().toISOString(),
      attachments: [],
      run_id: null,
      metadata,
    };
  }

  function summarizeCompletedReport(jobStatus: RuntimeJob, loadedArtifacts: JobArtifactsResponse): string {
    const risk = loadedArtifacts['risk_score.json'] as Record<string, unknown> | undefined;
    const quality = loadedArtifacts['quality_gate.json'] as Record<string, unknown> | undefined;
    const riskLevel = risk?.risk_level ?? risk?.overall_risk_level ?? '需查看报告';
    const gate = quality?.status ?? quality?.quality_gate ?? 'pass_with_warnings';
    return [
      '审查报告已生成。',
      '',
      `- 风险等级: ${String(riskLevel)}`,
      `- 审查质量状态: ${String(gate)}`,
      '- 证据缺口和引用详情请在右侧审查面板中查看。',
      '',
      '提示：本结果为非正式合规辅助分析，未人工复核，不构成正式法律意见。',
    ].join('\n');
  }

  async function runAssessment() {
    setBusy(true);
    setError(null);
    setReportError(null);
    setReportJobId(null);
    setReportStatus('validating');
    if (!health) {
      const reason = '后端 8012 未连接';
      setReportStatus('failed');
      setReportError(reason);
      setError(reason);
      setBusy(false);
      return;
    }
    if (!assessmentType) {
      const reason = '请选择评估类型';
      setReportStatus('failed');
      setReportError(reason);
      setError(reason);
      setBusy(false);
      return;
    }
    if (files.length === 0) {
      const reason = '请先上传业务材料';
      setReportStatus('failed');
      setReportError(reason);
      setError(reason);
      setBusy(false);
      return;
    }
    const notReady = files.find((file) => !['parsed', 'ready', 'completed'].includes(String(file.parse_status).toLowerCase()));
    if (notReady) {
      const reason = `文件仍在解析，请稍后：${notReady.original_filename}`;
      setReportStatus('failed');
      setReportError(reason);
      setError(reason);
      setBusy(false);
      return;
    }
    setEvents([]);
    setArtifacts(null);
    setArtifactDefaultTab('timeline');
    setArtifactDrawerCollapsed(false);
    isSendingRef.current = true;
    let runToken = conversationTokenRef.current;
    try {
      let convId = selectedConversationId;
      if (!convId) {
        const conversation = await reguthinkInteractiveClient.createConversation({
          title: `交互式诊断 ${new Date().toLocaleTimeString()}`,
          assessment_type: assessmentType,
        });
        convId = conversation.conversation_id;
        conversationTokenRef.current += 1;
        runToken = conversationTokenRef.current;
        setSelectedConversationId(convId);
      }
      const ownedFileIds = files.map((f) => f.file_id);
      const prompt = composerValue.trim() || '请基于当前上传材料和选择的评估类型生成非正式数据合规审查报告。';
      setReportStatus('creating_job');
      const requestStartedAt = performance.now();
      const response = await reguthinkInteractiveClient.chat(convId, {
        content: prompt,
        message: prompt,
        assessment_type: assessmentType,
        file_ids: ownedFileIds,
        auto_run_assessment: true,
        runtime_mode: 'full_chain_runtime',
        action: 'run_full_chain_report',
        rag_enabled: true,
        autojudge_enabled: true,
      });
      const responseMs = performance.now() - requestStartedAt;
      if (runToken !== conversationTokenRef.current) return;
      setComposerValue('');
      setLastChatResponse(response);
      setMessages((prev) => mergeMessages(prev, [response.user_message, response.assistant_message]));

      if (!response.job_id) {
        const reason = response.assistant_message?.content || '后端未返回审查任务编号';
        setReportStatus('failed');
        setReportError(reason);
        setJob(null);
        setEvents([]);
        setArtifacts(null);
        setArtifactDrawerCollapsed(true);
      }

      if (response.job_id) {
        setReportJobId(response.job_id);
        if (responseMs > 2000) {
          setReportError(`审查任务创建耗时 ${Math.round(responseMs)}ms，超过 2 秒硬门槛`);
        }
        const jobStatus = await reguthinkInteractiveClient.getJob(response.job_id);
        if (runToken !== conversationTokenRef.current) return;
        setJob(jobStatus);
        setReportStatus(jobStatus.status === 'completed' ? 'completed' : jobStatus.status === 'failed' ? 'failed' : 'running');
        setArtifactDrawerCollapsed(false);

        reguthinkInteractiveClient.streamJob(
          response.job_id,
          async (event) => {
            if (runToken !== conversationTokenRef.current) return;
            if (event.event_type !== 'final') {
              setEvents((current) => [...current, event as RuntimeEvent]);
            }
            const latest = await reguthinkInteractiveClient.getJob(response.job_id!);
            if (runToken !== conversationTokenRef.current) return;
            setJob(latest);
            setReportStatus(latest.status === 'completed' ? 'completed' : latest.status === 'failed' ? 'failed' : 'running');
            if (latest.status === 'failed') {
              setReportError(latest.error_message || event.message || '任务失败');
            }
            if (event.event_type === 'final') {
              const [eventLog, loadedArtifacts] = await Promise.all([
                reguthinkInteractiveClient.getJobEvents(response.job_id!),
                reguthinkInteractiveClient.getJobArtifacts(response.job_id!),
              ]);
              if (runToken !== conversationTokenRef.current) return;
              setEvents(eventLog.events);
              setArtifacts(loadedArtifacts);
              const finalJob = await reguthinkInteractiveClient.getJob(response.job_id!);
              if (runToken !== conversationTokenRef.current) return;
              setJob(finalJob);
              setReportStatus(finalJob.status === 'completed' ? 'completed' : 'failed');
              setArtifactDefaultTab(finalJob.status === 'completed' ? 'report' : 'timeline');
              setArtifactDrawerCollapsed(false);
              if (finalJob.status === 'completed') {
                setMessages((prev) => mergeMessages(prev, [
                  createLocalAssistantMessage(summarizeCompletedReport(finalJob, loadedArtifacts), {
                    local_report_summary: true,
                    job_id: finalJob.job_id,
                  }),
                ]));
              } else {
                const reason = finalJob.error_message || '任务失败';
                setReportError(reason);
                setMessages((prev) => mergeMessages(prev, [
                  createLocalAssistantMessage(`审查报告生成失败。\n\n- 失败原因: ${reason}`, {
                    local_report_failure: true,
                  }),
                ]));
              }
            }
          },
          (err) => {
            const reason = readableError(err);
            setError(reason);
            if (!reportJobId) setReportError(reason);
          }
        );
      }
      await refreshConversations();
    } catch (err) {
      const reason = readableError(err);
      setReportStatus('failed');
      setReportError(reason);
      setError(reason);
    } finally {
      isSendingRef.current = false;
      setBusy(false);
    }
  }

  function detectCrossBorderIntent(text: string): boolean {
    const lower = text.toLowerCase();
    return CROSS_BORDER_KEYWORDS.some((kw) => lower.includes(kw.toLowerCase()));
  }

  function handleSelectAssessment(type: string) {
    setAssessmentType(type as AssessmentType);
    setShowCrossBorderPrompt(false);
  }

  function handleSwitchToCrossBorder() {
    setAssessmentType('cross_border_data_transfer');
    setShowCrossBorderPrompt(false);
  }

  useEffect(() => {
    if (composerValue && detectCrossBorderIntent(composerValue) && assessmentType !== 'cross_border_data_transfer') {
      setShowCrossBorderPrompt(true);
    } else {
      setShowCrossBorderPrompt(false);
    }
  }, [composerValue, assessmentType]);

  function renderMainContent() {
    switch (activeView) {
      case 'agents':
        return <AgentClusterView job={job} artifacts={artifacts} />;
      case 'knowledge':
        return <KnowledgeGraphView job={job} artifacts={artifacts} />;
      case 'risk':
        return <RiskRadarView artifacts={artifacts} />;
      case 'import':
        return (
          <DataImportView
            conversationId={selectedConversationId}
            files={files}
            busy={busy}
            onCreateConversation={createConversation}
            onUpload={uploadFile}
            onOpenChat={() => onSelectView('chat')}
          />
        );
      case 'jobs':
        return <WorkspaceStatusView title="运行任务" job={job} artifacts={artifacts} events={events} />;
      case 'report':
        return <ReportCenterView conversationId={selectedConversationId} job={job} artifacts={artifacts} events={events} />;
      case 'boundaries':
        return <WorkspaceStatusView title="系统边界" job={job} artifacts={artifacts} events={events} />;
      case 'matrix':
        return <WorkspaceStatusView title="案例矩阵" job={job} artifacts={artifacts} events={events} />;
      case 'chat':
      default:
        return (
          <div className="chat-column" data-testid="chat-column">
            <ProductChatWorkspace
              hasConversation={!!selectedConversation}
              messages={messages}
              onSelectAssessment={handleSelectAssessment}
            />
            {showCrossBorderPrompt && (
              <div className="cross-border-prompt">
                <span className="cross-border-prompt-icon">🌐</span>
                <span>检测到跨境/出境场景，是否切换为<b>跨境数据传输评估</b>？</span>
                <button className="cross-border-switch-btn" type="button" onClick={handleSwitchToCrossBorder}>
                  切换
                </button>
                <button className="cross-border-dismiss-btn" type="button" onClick={() => setShowCrossBorderPrompt(false)}>
                  保留当前
                </button>
              </div>
            )}
            <div className="product-composer-wrapper">
              <ProductChatComposer
                value={composerValue}
                disabled={busy}
                running={job?.status === 'running' || job?.status === 'queued'}
                assessmentTypes={assessmentTypes}
                assessmentType={assessmentType}
                hasFiles={files.length > 0}
                files={files}
                intake={lastChatResponse?.uploaded_material_intake}
                reportStatus={reportStatus}
                reportJobId={reportJobId}
                reportError={reportError}
                onChange={setComposerValue}
                onSend={sendMessage}
                onUpload={uploadFile}
                onRemoveFile={removeFileFromCurrentContext}
                onRun={runAssessment}
                onAssessmentTypeChange={(t) => setAssessmentType(t as AssessmentType)}
                textareaRef={composerRef}
              />
            </div>
          </div>
        );
    }
  }

  const isChatLayout = activeView === 'chat';
  const showConversationRail = isChatLayout;
  const showRuntimePanel = isChatLayout;

  return (
    <div className={`product-workbench ${isChatLayout ? 'chat-layout' : 'workspace-layout'}`}>
      <ProductSidebar activeView={activeView} health={health} onSelectView={onSelectView} />
      {showConversationRail && (
        <ProductConversationRail
          conversations={conversations}
          selectedId={selectedConversationId}
          loading={loading}
          onCreate={() => createConversation()}
          onSelect={setSelectedConversationId}
          showAll={showAllConversations}
          onToggleShowAll={() => setShowAllConversations(!showAllConversations)}
        />
      )}
      <div className="product-main-area">
        <div className="be8-connection-badge" data-testid="be8-connection-badge">
          <span className={health ? 'ok' : 'warn'}>{health ? '审查服务正常' : '审查服务连接中'}</span>
          <span>知识库已连接</span>
        </div>
        {error && <div className="wb-error">{error}</div>}
        {renderMainContent()}
      </div>
      {showRuntimePanel && (
        <ProductArtifactDrawer
          artifacts={artifacts}
          chatResponse={lastChatResponse}
          job={job}
          events={events}
          defaultTab={artifactDefaultTab}
          collapsed={artifactDrawerCollapsed}
          onToggle={() => setArtifactDrawerCollapsed(!artifactDrawerCollapsed)}
        />
      )}
    </div>
  );
}

function WorkspaceStatusView({
  title,
  job,
  artifacts,
  events,
}: {
  title: string;
  job: RuntimeJob | null;
  artifacts: JobArtifactsResponse | null;
  events: RuntimeEvent[];
}) {
  const report = artifacts?.['user_report.md'] ?? artifacts?.['improved_report.md'];
  const evidence = artifacts?.['evidence_pack.json'];
  const citations = artifacts?.['citation_plan.json'];
  const review = artifacts?.['quality_gate.json'];
  return (
    <section className="workspace-page product-report-center">
      <div className="workspace-hero">
        <div>
          <p className="workspace-kicker">ReguThink Review</p>
          <h2>{title}</h2>
        </div>
        <div className={`workspace-job-pill ${job?.status || 'idle'}`}>
          {job ? translateJobStatus(job.status) : '等待开始'}
        </div>
      </div>
      <div className="workspace-dashboard-grid">
        <article className="workspace-panel">
          <h3>当前任务</h3>
          <div className="workspace-kv"><span>审查状态</span><strong>{job?.status || '暂无'}</strong></div>
          <div className="workspace-kv"><span>当前步骤</span><strong>{job?.current_stage || '等待开始'}</strong></div>
          <div className="workspace-kv"><span>完成度</span><strong>{job ? `${job.progress}%` : '0%'}</strong></div>
          <div className="workspace-kv"><span>进度记录</span><strong>{events.length}</strong></div>
        </article>
        <article className="workspace-panel">
          <h3>报告与评分</h3>
          <div className="workspace-kv"><span>用户报告</span><strong>{report ? '可下载' : '生成中'}</strong></div>
          <div className="workspace-kv"><span>证据整理</span><strong>{evidence ? '已生成' : '生成中'}</strong></div>
          <div className="workspace-kv"><span>引用整理</span><strong>{citations ? '已生成' : '生成中'}</strong></div>
          <div className="workspace-kv"><span>人工复核</span><strong>{review ? '未复核' : '等待报告'}</strong></div>
        </article>
      </div>
      {report ? <pre className="workspace-report-preview">{String(report).slice(0, 5000)}</pre> : null}
    </section>
  );
}

function translateJobStatus(status?: string) {
  if (status === 'completed') return '已完成';
  if (status === 'failed') return '失败';
  if (status === 'running') return '生成中';
  if (status === 'queued') return '排队中';
  return '等待开始';
}
