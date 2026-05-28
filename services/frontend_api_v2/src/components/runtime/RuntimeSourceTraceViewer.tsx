export function RuntimeSourceTraceViewer({ data }: { data: unknown }) {
  return (
    <section className="wb-mini-panel">
      <h3>来源说明</h3>
      <div className="wb-panel-note">来源记录仅用于辅助核查，不代表人工复核完成。</div>
      <div className="wb-placeholder">详细来源记录已归档在开发者诊断材料中。</div>
    </section>
  );
}
