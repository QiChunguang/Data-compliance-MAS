export function RuntimeManifestViewer({ data }: { data: unknown }) {
  return (
    <section className="wb-mini-panel">
      <h3>Runtime Manifest</h3>
      <pre className="wb-json">{JSON.stringify(data ?? { state: "missing" }, null, 2)}</pre>
    </section>
  );
}
