export function RuntimeRetrievalTraceViewer({ data }: { data: unknown }) {
  return (
    <section className="wb-mini-panel">
      <h3>Runtime RAG Trace</h3>
      <div className="wb-panel-note">BGE-M3 partially_effective; local neural reranker diagnostic_only / disabled by default.</div>
      <pre className="wb-json">{JSON.stringify(data ?? { state: "missing" }, null, 2)}</pre>
    </section>
  );
}
