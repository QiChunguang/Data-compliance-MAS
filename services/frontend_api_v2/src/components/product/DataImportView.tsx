import React, { useState } from 'react';
import type { AssessmentType, UploadedFile } from '../../types/reguthink-interactive-api';

const IMPORT_METHODS = [
  {
    name: '文件上传',
    status: 'available',
    desc: '支持 PDF、Word、TXT、Markdown 等格式',
    note: '仅作为业务事实输入',
  },
  {
    name: '数据库连接',
    status: 'pending',
    desc: 'MySQL、PostgreSQL、MongoDB',
    note: '后续接入',
  },
  {
    name: 'API 接入',
    status: 'pending',
    desc: 'RESTful API、GraphQL',
    note: '后续接入',
  },
  {
    name: '云存储同步',
    status: 'pending',
    desc: 'OSS、S3、Azure Blob',
    note: '后续接入',
  },
];

const UPLOAD_RULES = [
  '上传文件仅进入会话材料存储',
  '不写入法规知识库、图数据库或向量库',
  '不改变后端知识库指针',
  '最大文件大小限制：50MB',
  '支持格式：pdf, doc, docx, txt, md',
];

type Props = {
  conversationId: string;
  files: UploadedFile[];
  busy: boolean;
  onCreateConversation: (type?: AssessmentType) => Promise<string | undefined>;
  onUpload: (file: File, conversationId?: string) => Promise<string | undefined>;
  onOpenChat: () => void;
};

export const DataImportView: React.FC<Props> = ({
  conversationId,
  files,
  busy,
  onCreateConversation,
  onUpload,
  onOpenChat,
}) => {
  const [dragOver, setDragOver] = useState(false);
  const [status, setStatus] = useState<string>('等待上传');
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  async function handleFile(file?: File) {
    if (!file) return;
    setStatus('正在上传到当前会话...');
    let convId = conversationId;
    if (!convId) {
      convId = await onCreateConversation('data_transaction_compliance') || '';
    }
    const uploadedConversationId = await onUpload(file, convId);
    if (uploadedConversationId) {
      setStatus('上传成功，已加入当前会话材料');
    } else {
      setStatus('上传失败，请查看顶部错误信息');
    }
  }

  return (
    <div className="data-import-view">
      <div className="di-header">
        <h2>数据导入</h2>
        <p>上传材料用于同一会话的智能对话和报告生成</p>
      </div>

      <div className="di-grid">
        <div className="di-section">
          <h3>导入方式</h3>
          <div className="di-methods">
            {IMPORT_METHODS.map((method) => (
              <div key={method.name} className={`di-method ${method.status}`}>
                <div className="di-method-header">
                  <span className="di-method-name">{method.name}</span>
                  <span className={`di-method-badge ${method.status}`}>
                    {method.status === 'available' ? '可用' : '待接入'}
                  </span>
                </div>
                <p className="di-method-desc">{method.desc}</p>
                <span className="di-method-note">{method.note}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="di-section">
          <h3>上传区域</h3>
          <div
            className={`di-upload-zone ${dragOver ? 'dragover' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); void handleFile(e.dataTransfer.files?.[0]); }}
          >
            <div className="di-upload-icon">FILE</div>
            <p className="di-upload-text">拖拽文件到此处，或点击选择文件</p>
            <p className="di-upload-hint">支持 PDF、Word、TXT、Markdown</p>
            <input
              ref={fileInputRef}
              type="file"
              hidden
              accept=".pdf,.doc,.docx,.txt,.md"
              onChange={(e) => void handleFile(e.target.files?.[0])}
              data-testid="data-import-file-input"
            />
            <button
              className="di-upload-btn"
              type="button"
              disabled={busy}
              onClick={() => fileInputRef.current?.click()}
              data-testid="data-import-upload-button"
            >
              选择文件
            </button>
          </div>

          <div className="di-upload-status" data-testid="data-import-upload-status">
            {status}
          </div>

          {files.length > 0 && (
            <div className="di-current-files" data-testid="data-import-uploaded-files">
              <h4>当前会话材料</h4>
              {files.map((file) => (
                <div className="di-file-row" key={file.file_id}>
                  <strong>{file.original_filename}</strong>
                  <span>{file.parse_status}</span>
                </div>
              ))}
              <button className="di-upload-btn secondary" type="button" onClick={onOpenChat}>
                进入智能对话
              </button>
            </div>
          )}

          <div className="di-rules">
            <h4>上传规则</h4>
            <ul>
              {UPLOAD_RULES.map((rule) => (
                <li key={rule}>{rule}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="di-footer">
        <div className="di-hint">
          <span className="hint-badge">提示</span>
          <span>上传材料仅作为业务事实输入，不写入法规知识库。</span>
        </div>
      </div>
    </div>
  );
};
