import { useState } from "react";
import type { JobArtifactsResponse, RuntimeJob } from "../../types/reguthink-interactive-api";
import { RuntimeArtifactTabs } from "./RuntimeArtifactTabs";
import { RuntimeCitationViewer } from "./RuntimeCitationViewer";
import { RuntimeEvidenceViewer } from "./RuntimeEvidenceViewer";
import { RuntimeFailureNotice } from "./RuntimeFailureNotice";
import { RuntimeManifestViewer } from "./RuntimeManifestViewer";
import { RuntimeReportViewer } from "./RuntimeReportViewer";
import { RuntimeRetrievalTraceViewer } from "./RuntimeRetrievalTraceViewer";
import { RuntimeScoreViewer } from "./RuntimeScoreViewer";
import { RuntimeSourceTraceViewer } from "./RuntimeSourceTraceViewer";

function pickArtifact(artifacts: JobArtifactsResponse | null, names: string[]): unknown {
  if (!artifacts) {
    return null;
  }
  const artifactMap =
    typeof artifacts.artifacts === "object" && artifacts.artifacts !== null
      ? (artifacts.artifacts as Record<string, unknown>)
      : artifacts;
  for (const name of names) {
    if (Object.prototype.hasOwnProperty.call(artifactMap, name)) {
      const value = artifactMap[name];
      if (typeof value === "string" && (name.endsWith(".json") || value.trim().startsWith("{") || value.trim().startsWith("["))) {
        try {
          return JSON.parse(value);
        } catch {
          return value;
        }
      }
      return value;
    }
  }
  return { state: "missing", expected: names };
}

export function RealRuntimeResultPanel({
  job,
  artifacts,
}: {
  job: RuntimeJob | null;
  artifacts: JobArtifactsResponse | null;
}) {
  const [tab, setTab] = useState("Manifest");
  const isFailure = job?.status === "failed" || job?.error_message;

  return (
    <section className="real-runtime-panel">
      <div className="wb-panel-heading">
        <h2>Runtime Results</h2>
        <span>{job?.runtime_mode ?? "no job"}</span>
      </div>
      {isFailure && (
        <RuntimeFailureNotice
          status={job?.status ?? "runtime_not_configured"}
          message={job?.error_message ?? "runtime_contract_not_supported or runtime_adapter_not_configured"}
        />
      )}
      <RuntimeArtifactTabs active={tab} onChange={setTab} />
      {tab === "Manifest" && <RuntimeManifestViewer data={pickArtifact(artifacts, ["runtime_manifest", "runtime_manifest.json", "manifest"])} />}
      {tab === "Report" && <RuntimeReportViewer data={pickArtifact(artifacts, ["report", "report.md"])} />}
      {tab === "Evidence" && <RuntimeEvidenceViewer data={pickArtifact(artifacts, ["evidence_pack", "evidence_pack.json"])} />}
      {tab === "Citations" && <RuntimeCitationViewer data={pickArtifact(artifacts, ["citation_plan", "citation_plan.json"])} />}
      {tab === "Score" && <RuntimeScoreViewer data={pickArtifact(artifacts, ["score", "score.json", "autojudge_result", "autojudge_result.json"])} />}
      {tab === "Source Trace" && <RuntimeSourceTraceViewer data={pickArtifact(artifacts, ["source_trace", "source_trace.json"])} />}
      {tab === "RAG Trace" && <RuntimeRetrievalTraceViewer data={pickArtifact(artifacts, ["retrieval_trace", "retrieval_trace.json"])} />}
      {tab === "LLM Judge" && <RuntimeScoreViewer data={pickArtifact(artifacts, ["llm_judge_result", "llm_judge_result.json"])} />}
    </section>
  );
}
