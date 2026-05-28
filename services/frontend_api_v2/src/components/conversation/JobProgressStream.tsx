import type { RuntimeJob } from "../../types/reguthink-interactive-api";

export function JobProgressStream({ job }: { job: RuntimeJob | null }) {
  if (!job) {
    return <div className="wb-placeholder">No job started.</div>;
  }
  return (
    <section className="job-progress">
      <div>
        <strong>{job.status}</strong>
        <span>{job.current_stage}</span>
      </div>
      <progress value={job.progress} max={100} />
      {job.error_message && <div className="wb-error">{job.error_message}</div>}
    </section>
  );
}
