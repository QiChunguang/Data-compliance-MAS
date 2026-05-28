type CommandBarProps = {
  value: string;
  runtimeEnabled: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onTab: (tab: string) => void;
};

export function CommandBar({ value, runtimeEnabled, onChange, onSubmit, onTab }: CommandBarProps) {
  return (
    <footer className="wb-command-bar">
      <div className="wb-command-input-wrap">
        <span className="wb-command-prefix">/case</span>
        <input
          aria-label="case id or keyword"
          className="wb-command-input"
          placeholder="输入 case_id / keyword，Enter 后筛选"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              onSubmit();
            }
          }}
        />
      </div>
      <div className="wb-command-actions">
        <button type="button" onClick={() => onTab("report")}>查看报告</button>
        <button type="button" onClick={() => onTab("evidence")}>查看证据</button>
        <button type="button" onClick={() => onTab("score")}>查看评分</button>
        <button type="button" disabled={!runtimeEnabled} title="runtime disabled in FE2 / diagnostic only">
          Dry-run
        </button>
      </div>
    </footer>
  );
}
