import React from "react";
import { FileUploadButton } from "./FileUploadButton";

type Props = {
  value: string;
  disabled: boolean;
  running: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
  onUpload: (file: File) => void;
  onRun: () => void;
};

export function ChatComposer({ value, disabled, running, onChange, onSend, onUpload, onRun }: Props) {
  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  }

  return (
    <div className="gpt-composer">
      <div className="composer-box">
        <div className="composer-row">
          <FileUploadButton disabled={disabled || running} onUpload={onUpload} />
          <textarea
            value={value}
            disabled={disabled}
            placeholder="请输入你的数据交易、跨境传输、个人信息处理或数据流通安全问题..."
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={handleKeyDown}
            className="gpt-textarea"
            rows={1}
          />
          <div className="composer-actions">
            <button
              type="button"
              className="run-btn"
              disabled={disabled || running}
              onClick={onRun}
            >
              🔍 评估
            </button>
            <button
              type="button"
              className="send-btn"
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
}
