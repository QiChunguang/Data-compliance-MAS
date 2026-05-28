export function RuntimeBoundaryNotice() {
  return (
    <section className="runtime-boundary-notice">
      <strong>prototype diagnostic</strong>
      <span>not production-ready</span>
      <span>not source-backed pass</span>
      <span>not human-reviewed</span>
      <span>uploaded files do not enter Chroma / Neo4j / current_backend</span>
      <span>source trace is not manual verification</span>
    </section>
  );
}
