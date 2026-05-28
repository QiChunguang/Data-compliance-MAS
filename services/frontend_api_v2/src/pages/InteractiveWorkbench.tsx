import { useEffect, useMemo, useState } from "react";
import { reguthinkClient } from "../api/reguthinkClient";
import { ReguThinkInteractiveError, reguthinkInteractiveClient } from "../api/reguthinkInteractiveClient";
import { AssessmentTypeSelector } from "../components/conversation/AssessmentTypeSelector";
import { ChatComposer } from "../components/conversation/ChatComposer";
import { ChatThread } from "../components/conversation/ChatThread";
import { ConversationList } from "../components/conversation/ConversationList";
import { JobArtifactPanel } from "../components/conversation/JobArtifactPanel";
import { JobProgressStream } from "../components/conversation/JobProgressStream";
import { RuntimeEventTimeline } from "../components/conversation/RuntimeEventTimeline";
import { UploadedFileList } from "../components/conversation/UploadedFileList";
import { Sidebar } from "../components/layout/Sidebar";
import { TopBar } from "../components/layout/TopBar";
import { AssessmentRunPanel } from "../components/runtime/AssessmentRunPanel";
import { RealRuntimeResultPanel } from "../components/runtime/RealRuntimeResultPanel";
import { RuntimeBoundaryNotice } from "../components/runtime/RuntimeBoundaryNotice";
import type { BaselineStatusResponse, HealthResponse } from "../types/reguthink-api";
import type {
  AssessmentType,
  AssessmentTypeInfo,
  Conversation,
  JobArtifactsResponse,
  Message,
  RuntimeEvent,
  RuntimeJob,
  UploadedFile,
} from "../types/reguthink-interactive-api";

const DEFAULT_ASSESSMENT: AssessmentType = "data_transaction_compliance";

const QUICK_TASKS = [
  {
    id: "data_transaction_compliance" as AssessmentType,
    title: "数据交易合规评估",
    description: "评估数据交易场景的合规性风险",
  },
  {
    id: "data_flow_security_review" as AssessmentType,
    title: "数据流通安全审查",
    description: "审查数据流通的安全风险",
  },
  {
    id: "cross_border_data_transfer" as AssessmentType,
    title: "跨境数据传输评估",
    description: "评估跨境数据传输的合规性",
  },
  {
    id: "pipl_personal_information_protection" as AssessmentType,
    title: "PIPL 个人信息保护",
    description: "评估个人信息保护合规性",
  },
];

function readableError(error: unknown): string {
  if (error instanceof ReguThinkInteractiveError) {
    return `${error.kind}: ${error.message}`;
  }
  return error instanceof Error ? error.message : "Unknown error";
}

type Props = {
  activeView: string;
  onSelectView: (view: string) => void;
};

export function InteractiveWorkbench({ activeView, onSelectView }: Props) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [baseline, setBaseline] = useState<BaselineStatusResponse | null>(null);
  const [assessmentTypes, setAssessmentTypes] = useState<AssessmentTypeInfo[]>([]);
  const [assessmentType, setAssessmentType] = useState<AssessmentType>(DEFAULT_ASSESSMENT);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [events, setEvents] = useState<RuntimeEvent[]>([]);
  const [job, setJob] = useState<RuntimeJob | null>(null);
  const [artifacts, setArtifacts] = useState<JobArtifactsResponse | null>(null);
  const [composerValue, setComposerValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAllConversations, setShowAllConversations] = useState(false);

  const selectedConversation = useMemo(
    () => conversations.find((item) => item.conversation_id === selectedConversationId) ?? null,
    [conversations, selectedConversationId],
  );

  async function refreshConversations(nextSelectedId?: string) {
    const list = await reguthinkInteractiveClient.listConversations();
    setConversations(list);
    const selected = nextSelectedId || selectedConversationId || list[0]?.conversation_id || "";
    setSelectedConversationId(selected);
    return selected;
  }

  async function loadConversation(conversationId: string) {
    if (!conversationId) {
      return;
    }
    const [messageList, fileList] = await Promise.all([
      reguthinkInteractiveClient.getMessages(conversationId),
      reguthinkInteractiveClient.listFiles(conversationId),
    ]);
    setMessages(messageList);
    setFiles(fileList);
  }

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
        setConversations(conversationList);
        // 默认不选中任何会话，显示欢迎页！
        setSelectedConversationId("");
      } catch (err) {
        setError(readableError(err));
      } finally {
        setLoading(false);
      }
    }

    void boot();
  }, []);

  useEffect(() => {
    if (selectedConversationId) {
      void loadConversation(selectedConversationId).catch((err) => setError(readableError(err)));
    }
  }, [selectedConversationId]);

  async function createConversation(type?: AssessmentType) {
    setBusy(true);
    setError(null);
    try {
      const conversation = await reguthinkInteractiveClient.createConversation({
        title: `交互式诊断 ${new Date().toLocaleTimeString()}`,
        assessment_type: type ?? assessmentType,
      });
      if (type) {
        setAssessmentType(type);
      }
      const selected = await refreshConversations(conversation.conversation_id);
      await loadConversation(selected);
    } catch (err) {
      setError(readableError(err));
    } finally {
      setBusy(false);
    }
  }

  async function sendMessage() {
    if (!composerValue.trim()) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      let convId = selectedConversationId;
      if (!convId) {
        const conversation = await reguthinkInteractiveClient.createConversation({
          title: `交互式诊断 ${new Date().toLocaleTimeString()}`,
          assessment_type: assessmentType,
        });
        convId = conversation.conversation_id;
        setSelectedConversationId(convId);
        await refreshConversations(convId);
      }
      await reguthinkInteractiveClient.sendMessage(convId, composerValue.trim(), files.map((file) => file.file_id));
      setComposerValue("");
      await loadConversation(convId);
      await refreshConversations(convId);
    } catch (err) {
      setError(readableError(err));
    } finally {
      setBusy(false);
    }
  }

  async function uploadFile(file: File) {
    setBusy(true);
    setError(null);
    try {
      let convId = selectedConversationId;
      if (!convId) {
        const conversation = await reguthinkInteractiveClient.createConversation({
          title: `交互式诊断 ${new Date().toLocaleTimeString()}`,
          assessment_type: assessmentType,
        });
        convId = conversation.conversation_id;
        setSelectedConversationId(convId);
        await refreshConversations(convId);
      }
      await reguthinkInteractiveClient.uploadFile(convId, file);
      await loadConversation(convId);
      await refreshConversations(convId);
    } catch (err) {
      setError(readableError(err));
    } finally {
      setBusy(false);
    }
  }

  async function runAssessment() {
    setBusy(true);
    setError(null);
    setEvents([]);
    setArtifacts(null);
    try {
      let convId = selectedConversationId;
      if (!convId) {
        const conversation = await reguthinkInteractiveClient.createConversation({
          title: `交互式诊断 ${new Date().toLocaleTimeString()}`,
          assessment_type: assessmentType,
        });
        convId = conversation.conversation_id;
        setSelectedConversationId(convId);
        await refreshConversations(convId);
      }
      const prompt = composerValue.trim() || messages[messages.length - 1]?.content || "执行合规评估。";
      const created = await reguthinkInteractiveClient.runAssessment(convId, {
        assessment_type: assessmentType,
        user_prompt: prompt,
        file_ids: files.map((file) => file.file_id),
        runtime_mode: "dry_run",
      });
      setComposerValue("");
      const jobStatus = await reguthinkInteractiveClient.getJob(created.job_id);
      setJob(jobStatus);

      reguthinkInteractiveClient.streamJob(
        created.job_id,
        async (event) => {
          if (event.event_type !== "final") {
            setEvents((current) => [...current, event as RuntimeEvent]);
          }
          const latest = await reguthinkInteractiveClient.getJob(created.job_id);
          setJob(latest);
          if (event.event_type === "final") {
            const [eventLog, loadedArtifacts] = await Promise.all([
              reguthinkInteractiveClient.getJobEvents(created.job_id),
              reguthinkInteractiveClient.getJobArtifacts(created.job_id),
            ]);
            setEvents(eventLog.events);
            setArtifacts(loadedArtifacts);
          }
        },
        (err) => {
          setError(readableError(err));
        },
      );
    } catch (err) {
      setError(readableError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="gpt-workbench">
      <Sidebar activeView={activeView} health={health} onSelectView={onSelectView} />
      <div className="conversation-rail">
        <div className="rail-header">
          <h2>会话</h2>
          <button className="new-conversation-btn" type="button" onClick={() => void createConversation()}>
            + 新建诊断
          </button>
        </div>
        <ConversationList
          conversations={conversations}
          selectedId={selectedConversationId}
          loading={loading}
          onCreate={createConversation}
          onSelect={setSelectedConversationId}
          showAll={showAllConversations}
          onToggleShowAll={() => setShowAllConversations(!showAllConversations)}
        />
      </div>
      <div className="main-workspace">
        <TopBar selectedCase={null} health={health} baseline={baseline} isInteractive={true} />
        <main className="chat-area">
          {error && <div className="wb-error">{error}</div>}
          <RuntimeBoundaryNotice />

          {!selectedConversation && !loading && (
            <div className="welcome-section">
              <div className="welcome-content">
                <div className="welcome-logo">
                  <div className="logo-mark">RT</div>
                </div>
                <h1>您好，有什么可以帮您？</h1>
                <p className="welcome-desc">选择一个评估类型开始进行合规评估。</p>
                <div className="quick-task-grid">
                  {QUICK_TASKS.map((task) => (
                    <button
                      key={task.id}
                      className="quick-task-card"
                      type="button"
                      onClick={() => {
                        void createConversation(task.id);
                      }}
                    >
                      <span className="task-title">{task.title}</span>
                      <span className="task-desc">{task.description}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="welcome-footer">
                <div className="footer-hint">
                  <span className="hint-badge">提示</span>
                  <span>当前系统为 prototype diagnostic，不是正式法律意见。</span>
                </div>
              </div>
            </div>
          )}

          {selectedConversation && (
            <div className="chat-content">
              <div className="chat-toolbar">
                <div className="toolbar-left">
                  <AssessmentTypeSelector
                    value={assessmentType}
                    types={assessmentTypes}
                    onChange={setAssessmentType}
                  />
                </div>
                <div className="status-badges">
                  {health?.runtime_enabled ? (
                    <span className="wb-chip warning">dry-run 模式</span>
                  ) : (
                    <span className="wb-chip warning">runtime disabled</span>
                  )}
                  <span className="wb-chip danger">not formal legal opinion</span>
                </div>
              </div>
              <ChatThread messages={messages} />
              {events.length > 0 && <RuntimeEventTimeline events={events} />}
              {job && <JobProgressStream job={job} />}
              {artifacts && (
                <div className="artifact-section">
                  <JobArtifactPanel artifacts={artifacts} />
                  <RealRuntimeResultPanel job={job} artifacts={artifacts} />
                </div>
              )}
              {selectedConversation && (
                <div className="composer-top">
                  <UploadedFileList files={files} />
                </div>
              )}
            </div>
          )}

          {/* ChatComposer 始终显示在底部 */}
          <div className="composer-wrapper">
            <div className="composer-toolbar">
              <AssessmentTypeSelector
                value={assessmentType}
                types={assessmentTypes}
                onChange={setAssessmentType}
              />
              <div className="status-badges-inline">
                {health?.runtime_enabled ? (
                  <span className="wb-chip warning">dry-run 模式</span>
                ) : (
                  <span className="wb-chip warning">runtime disabled</span>
                )}
                <span className="wb-chip danger">not formal legal opinion</span>
              </div>
            </div>
            <ChatComposer
              value={composerValue}
              disabled={busy}
              running={job?.status === "running" || job?.status === "queued"}
              onChange={setComposerValue}
              onSend={sendMessage}
              onUpload={uploadFile}
              onRun={() => void runAssessment()}
            />
          </div>
        </main>
      </div>
    </div>
  );
}
