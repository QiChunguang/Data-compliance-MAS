import React from 'react';
import { FileUploadButton } from '../conversation/FileUploadButton';
import type {
  AssessmentType,
  AssessmentTypeInfo,
  ChatResponse,
  UploadedFile,
} from '../../types/reguthink-interactive-api';

export type ReportTriggerStatus = 'idle' | 'validating' | 'creating_job' | 'running' | 'completed' | 'failed';

type ProductChatComposerProps = {
  value: string;
  disabled: boolean;
  running: boolean;
  assessmentTypes: AssessmentTypeInfo[];
  assessmentType: AssessmentType;
  hasFiles: boolean;
  files: UploadedFile[];
  intake?: ChatResponse['uploaded_material_intake'];
  reportStatus: ReportTriggerStatus;
  reportJobId?: string | null;
  reportError?: string | null;
  onChange: (value: string) => void;
  onSend: () => void;
  onUpload: (file: File) => void;
  onRemoveFile: (fileId: string) => void;
  onRun: () => void;
  onAssessmentTypeChange: (type: AssessmentType) => void;
  textareaRef?: React.RefObject<HTMLTextAreaElement | null>;
};

export const ProductChatComposer: React.FC<ProductChatComposerProps> = ({
  value,
  disabled,
  running,
  hasFiles,
  files,
  intake,
  reportStatus,
  reportError,
  onChange,
  onSend,
  onUpload,
  onRemoveFile,
  onRun,
  textareaRef,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const runLabel = {
    idle: '生成审查报告',
    validating: '检查材料...',
    creating_job: '创建任务...',
    running: '审查生成中...',
    completed: '重新生成报告',
    failed: '生成失败，查看原因',
  }[reportStatus];
  const reportBusy = reportStatus === 'validating' || reportStatus === 'creating_job' || reportStatus === 'running';

  return (
    <div className="product-chat-composer" data-testid="chat-composer-shell">
      {hasFiles && (
        <MaterialReadyCard
          files={files}
          intake={intake}
          reportStatus={reportStatus}
          reportError={reportError}
          onRemoveFile={onRemoveFile}
        />
      )}

      <div className="product-composer-toolbar">
        <div className="product-composer-assessment-selector">
          <span className="product-badge info">非正式合规辅助分析</span>
        </div>
        <div className="product-composer-badges">
          <span className="product-badge info">发送=普通聊天</span>
          <span className="product-badge warning">报告=完整审查</span>
          <span className="product-badge danger">需人工复核</span>
        </div>
      </div>

      {hasFiles && (
        <div className="product-composer-disclaimer">
          <span className="disclaimer-icon">ready</span>
          <span className="disclaimer-text">
            材料已解析，可先普通提问，也可生成审查报告。上传材料只作为业务事实，不写入法规库。
          </span>
        </div>
      )}

      <div className="product-composer-box">
        <div className="product-composer-row">
          <div className="product-composer-upload">
            <FileUploadButton disabled={disabled || running} onUpload={onUpload} />
          </div>

          <textarea
            ref={textareaRef}
            className="product-composer-textarea"
            data-testid="chat-composer-input"
            value={value}
            disabled={disabled}
            placeholder="请输入您的问题，ReguThink 将基于材料和合规知识库提供辅助分析……"
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />

          <div className="product-composer-actions">
            <button
              className={`product-run-btn report-${reportStatus}`}
              type="button"
              disabled={disabled || reportBusy}
              onClick={onRun}
              data-testid="report-trigger-button"
            >
              {runLabel}
            </button>
            <button
              className="product-send-btn"
              type="button"
              disabled={disabled || !value.trim()}
              onClick={onSend}
            >
              发送
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

function MaterialReadyCard({
  files,
  intake,
  reportStatus,
  reportError,
  onRemoveFile,
}: {
  files: UploadedFile[];
  intake?: ChatResponse['uploaded_material_intake'];
  reportStatus: ReportTriggerStatus;
  reportError?: string | null;
  onRemoveFile: (fileId: string) => void;
}) {
  const [expanded, setExpanded] = React.useState(false);
  const parsedCount = files.filter((file) => ['parsed', 'ready', 'completed'].includes(String(file.parse_status).toLowerCase())).length;
  const canRun = files.length > 0 && parsedCount === files.length;
  const missing = intake?.missing_information || [];
  const dataTypes = intake?.data_type || [];
  const parties = intake?.parties || [];
  return (
    <section className="material-ready-card" data-testid="material-compact-card">
      <div className="material-ready-main">
        <div className="material-ready-icon">MAT</div>
        <div className="material-ready-copy">
          <div className="material-ready-title">
            已上传 {files.length} 个业务材料
            <span className={`material-ready-status ${canRun ? 'ready' : 'parsing'}`}>
              {canRun ? '已解析' : '解析中'}
            </span>
          </div>
          <div className="material-ready-subtitle">
            {files.map((file) => file.original_filename).join(' / ')}
          </div>
        </div>
        <div className="material-ready-actions">
          <button type="button" onClick={() => setExpanded((value) => !value)}>
            {expanded ? '收起详情' : '查看详情'}
          </button>
          <button type="button" disabled title="当前无重新解析后端接口">
            重新解析
          </button>
        </div>
      </div>

      {expanded && (
        <>
          <div className="material-summary-strip">
            <span>交易方 {parties.length ? '已识别' : '待补充'}</span>
            <span>数据类型 {dataTypes.length ? dataTypes.slice(0, 2).join(', ') : '待识别'}</span>
            <span>缺失信息 {missing.length || 0}</span>
            <span>{canRun ? '可生成审查报告' : '等待解析完成'}</span>
          </div>

          <div className="material-boundary-chips">
            <span>业务事实材料</span>
            <span>不写入法规库</span>
            <span>未人工复核</span>
            <span>非正式法律意见</span>
          </div>
        </>
      )}

      {(reportError || reportStatus !== 'idle') && (
        <div className={`material-report-status ${reportStatus}`} data-testid="report-trigger-status">
          <span>{reportStatus === 'completed' ? '报告已完成' : reportStatus === 'running' ? '报告生成中' : reportStatus === 'failed' ? '生成失败' : '准备生成'}</span>
          {reportError && <em>{reportError}</em>}
        </div>
      )}

      {expanded && (
        <div className="material-details-panel" data-testid="material-debug-details">
          {files.map((file) => (
            <article key={file.file_id} className="material-detail-file">
              <div>
                <strong>{file.original_filename}</strong>
                <span>{file.parse_status} · {Math.round(file.size_bytes / 1024)} KB</span>
              </div>
              <button type="button" onClick={() => onRemoveFile(file.file_id)}>移除文件</button>
            </article>
          ))}
          {intake && (
            <div className="material-boundary-chips">
              <span>仅作业务事实</span>
              <span>不写入法规知识库</span>
              <span>等待人工复核</span>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
