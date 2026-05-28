const TABS = ["Manifest", "Report", "Evidence", "Citations", "Score", "Source Trace", "RAG Trace", "LLM Judge"];

type Props = {
  active: string;
  onChange: (value: string) => void;
};

export function RuntimeArtifactTabs({ active, onChange }: Props) {
  return (
    <div className="runtime-artifact-tabs">
      {TABS.map((tab) => (
        <button className={active === tab ? "active" : ""} key={tab} type="button" onClick={() => onChange(tab)}>
          {tab}
        </button>
      ))}
    </div>
  );
}
