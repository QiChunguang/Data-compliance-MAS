import type { RuntimeJob } from "../../types/reguthink-interactive-api";
import { RuntimeModeBadge } from "./RuntimeModeBadge";

export function AssessmentRunPanel({ job }: { job: RuntimeJob | null }) {
  return (
    <section className="wb-mini-panel">
      <h3>Assessment Run</h3>
      {job ? (
        <div className="runtime-run-grid">
          <span>job_id</span>
          <strong>{job.job_id}</strong>
          <span>mode</span>
          <RuntimeModeBadge mode={job.runtime_mode} />
          <span>status</span>
          <strong>{job.status}</strong>
          <span>stage</span>
          <strong>{job.current_stage}</strong>
        </div>
      ) : (
        <div className="wb-placeholder">Run a dry-run assessment to create a job.</div>
      )}
    </section>
  );
}
