import type { JobArtifactsResponse } from "../../types/reguthink-interactive-api";

export function JobArtifactPanel({ artifacts }: { artifacts: JobArtifactsResponse | null }) {
  return (
    <section className="wb-mini-panel artifact-panel">
      <h3>Job Artifacts</h3>
      <div className="wb-warning-line">Artifacts are diagnostic outputs, not formal legal opinions.</div>
      {artifacts ? (
        <pre className="wb-json">{JSON.stringify(artifacts, null, 2)}</pre>
      ) : (
        <div className="wb-placeholder">No artifacts loaded yet. Missing and placeholder states stay visible.</div>
      )}
    </section>
  );
}
