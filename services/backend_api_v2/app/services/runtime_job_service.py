from __future__ import annotations

import threading
from typing import Any, Dict, List
from uuid import uuid4

from app.core.boundaries import BOUNDARY_FLAGS
from app.models.chat import utc_now
from app.models.job import JobStatus, RunAssessmentRequest, RuntimeJob, RuntimeMode
from app.services.assessment_intent_service import AssessmentIntentService
from app.services.assessment_router_service import AssessmentRouterService
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.conversation_service import ConversationService
from app.services.file_upload_service import FileUploadService
from app.services.multi_agent_runtime_adapter import MultiAgentRuntimeAdapter
from app.services.prototype_advice_service import PrototypeAdviceService
from app.services.runtime_event_service import RuntimeEventService
from app.services.runtime_storage import RuntimeStorage
from app.services.storage_utils import write_json_atomic
from app.services.uploaded_material_intake_service import UploadedMaterialIntakeService
from app.services.multi_agent_runtime_orchestrator import MultiAgentRuntimeOrchestrator
from app.services.full_chain_runtime_orchestrator import FullChainRuntimeOrchestrator


class RuntimeJobService:
    def __init__(self) -> None:
        self.storage = RuntimeStorage()
        self.events = RuntimeEventService()
        self.conversations = ConversationService()
        self.files = FileUploadService()
        self.assessments = AssessmentRouterService()
        self.adapter = MultiAgentRuntimeAdapter()
        self.intent_service = AssessmentIntentService()
        self.intake_service = UploadedMaterialIntakeService()
        self.advice_service = PrototypeAdviceService()
        self.orchestrator = MultiAgentRuntimeOrchestrator()
        self.full_chain_orchestrator = FullChainRuntimeOrchestrator()
        self.memory = ConversationMemoryService()

    def create_and_run(self, conversation_id: str, req: RunAssessmentRequest) -> RuntimeJob:
        self.conversations.require_conversation(conversation_id)
        if req.runtime_mode == RuntimeMode.full_chain_runtime:
            req = req.model_copy(update={"autojudge_enabled": True})
        job = RuntimeJob(
            job_id=f"job_{uuid4().hex}",
            conversation_id=conversation_id,
            assessment_type=req.assessment_type,
            input_files=req.file_ids,
            user_prompt=req.user_prompt,
            boundary_flags=BOUNDARY_FLAGS,
            runtime_mode=req.runtime_mode,
        )
        self._save_job(job)
        if req.runtime_mode == RuntimeMode.controlled_runtime and not self.adapter.can_run_controlled_runtime():
            return self._fail_controlled_runtime(job)
        if req.runtime_mode == RuntimeMode.controlled_runtime:
            return self._run_controlled_job(job, req)
        if req.runtime_mode == RuntimeMode.uploaded_material_runtime:
            return self._run_uploaded_material_job(job, req)
        if req.runtime_mode == RuntimeMode.full_chain_runtime:
            return self._run_full_chain_job(job, req)
        return self._run_dry_job(job, req)

    def create_async(self, conversation_id: str, req: RunAssessmentRequest) -> RuntimeJob:
        """Create a local prototype background job and return immediately.

        This is intentionally an in-process local async runner, not a production
        durable queue. Job state and SSE events are persisted to JSON/JSONL so
        the browser can recover progress while the dev server remains alive.
        """
        self.conversations.require_conversation(conversation_id)
        if req.runtime_mode == RuntimeMode.full_chain_runtime:
            req = req.model_copy(update={"autojudge_enabled": True})
        job = RuntimeJob(
            job_id=f"job_{uuid4().hex}",
            conversation_id=conversation_id,
            assessment_type=req.assessment_type,
            input_files=req.file_ids,
            user_prompt=req.user_prompt,
            boundary_flags=BOUNDARY_FLAGS,
            runtime_mode=req.runtime_mode,
            current_stage="queued",
        )
        self._save_job(job)
        self.events.add_event(
            job.job_id,
            "job_created",
            "queued",
            "Local prototype async job created; background full-chain execution will start without blocking the HTTP response.",
            {"async_job": True, "not_production_queue": True},
        )
        worker = threading.Thread(
            target=self._execute_async_job,
            args=(job.job_id, req),
            name=f"reguthink-{job.job_id}",
            daemon=True,
        )
        worker.start()
        return job

    def _execute_async_job(self, job_id: str, req: RunAssessmentRequest) -> None:
        try:
            job = self.require_job(job_id)
            if job.status == JobStatus.cancelled:
                return
            if req.runtime_mode == RuntimeMode.full_chain_runtime:
                self._run_full_chain_job(job, req)
            elif req.runtime_mode == RuntimeMode.uploaded_material_runtime:
                self._run_uploaded_material_job(job, req)
            elif req.runtime_mode == RuntimeMode.controlled_runtime:
                if not self.adapter.can_run_controlled_runtime():
                    self._fail_controlled_runtime(job)
                else:
                    self._run_controlled_job(job, req)
            else:
                self._run_dry_job(job, req)
        except Exception as exc:
            try:
                job = self.require_job(job_id)
                self.events.add_event(job_id, "job_failed", "failed", f"Async job failed: {type(exc).__name__}: {exc}")
                self.events.add_event(job_id, "final", "failed", "Final event: async job failed.")
                job = job.model_copy(
                    update={
                        "status": JobStatus.failed,
                        "completed_at": utc_now(),
                        "progress": 100,
                        "current_stage": "failed",
                        "error_message": f"async_job_failed:{type(exc).__name__}",
                    }
                )
                self._save_job(job)
            except Exception:
                return

    def get_job(self, job_id: str) -> RuntimeJob | None:
        path = self.storage.job_json(job_id)
        if not path.exists():
            return None
        return RuntimeJob.model_validate_json(path.read_text(encoding="utf-8"))

    def latest_for_conversation(self, conversation_id: str) -> RuntimeJob | None:
        latest: RuntimeJob | None = None
        jobs_root = self.storage.ensure() / "jobs"
        for path in jobs_root.glob("job_*/job.json"):
            try:
                job = RuntimeJob.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if job.conversation_id != conversation_id:
                continue
            if latest is None or job.created_at > latest.created_at:
                latest = job
        return latest

    def list_for_conversation(self, conversation_id: str) -> List[RuntimeJob]:
        jobs: List[RuntimeJob] = []
        jobs_root = self.storage.ensure() / "jobs"
        for path in jobs_root.glob("job_*/job.json"):
            try:
                job = RuntimeJob.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if job.conversation_id == conversation_id:
                jobs.append(job)
        return sorted(jobs, key=lambda item: item.created_at, reverse=True)

    def require_job(self, job_id: str) -> RuntimeJob:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(f"Unknown job_id: {job_id}")
        return job

    def cancel(self, job_id: str) -> RuntimeJob:
        job = self.require_job(job_id)
        if job.status not in {JobStatus.completed, JobStatus.failed, JobStatus.cancelled}:
            job = job.model_copy(update={"status": JobStatus.cancelled, "completed_at": utc_now(), "current_stage": "cancelled"})
            self.events.add_event(job_id, "job_cancelled", "cancelled", "Job was cancelled by request.")
            self.events.add_event(job_id, "final", "cancelled", "Final event: job cancelled.")
            self._save_job(job)
        return job

    def artifacts(self, job_id: str) -> Dict[str, Any]:
        job = self.require_job(job_id)
        result: Dict[str, Any] = {"job": job.model_dump(mode="json"), "artifacts": {}}
        artifacts_dir = self.storage.artifacts_dir(job_id)
        for path in artifacts_dir.glob("*"):
            if path.is_file():
                result["artifacts"][path.name] = path.read_text(encoding="utf-8", errors="replace")
        return result

    def _run_dry_job(self, job: RuntimeJob, req: RunAssessmentRequest) -> RuntimeJob:
        job = job.model_copy(update={"status": JobStatus.running, "started_at": utc_now(), "progress": 3, "current_stage": "job_created"})
        self._save_job(job)
        self.events.add_event(job.job_id, "job_created", "job_created", "Dry-run diagnostic job created.", self.adapter.plan(req.runtime_mode))

        stage = 8
        self.events.add_event(job.job_id, "user_prompt_received", "user_prompt_received", "User prompt received.", {"prompt_length": len(req.user_prompt)})
        job = self._progress(job, stage := stage + 5)
        self.events.add_event(job.job_id, "uploaded_materials_loaded", "uploaded_materials_loaded", "Uploaded materials loaded into preview.", {"file_ids": req.file_ids})
        job = self._progress(job, stage := stage + 5)

        file_records = [self.files.get_file(file_id) for file_id in req.file_ids]
        valid_files = [item for item in file_records if item is not None]
        previews = [
            {"file_id": item.file_id, "display_path": item.display_path, "parse_status": item.parse_status}
            for item in valid_files
        ]

        self.events.add_event(job.job_id, "material_intake_started", "material_intake_started", "Starting uploaded material intake analysis.")
        job = self._progress(job, stage := stage + 5)
        intake = self.intake_service.intake(valid_files, req.user_prompt)
        self.events.add_event(job.job_id, "material_intake_completed", "material_intake_completed", "Uploaded material intake completed.", intake.model_dump(mode="json"))
        job = self._progress(job, stage := stage + 5)

        intent = self.intent_service.detect(req.user_prompt)
        self.events.add_event(job.job_id, "assessment_intent_detected", "assessment_intent_detected", "Assessment intent detected.", {"detected_type": intent.detected_type, "confidence": intent.confidence})
        job = self._progress(job, stage := stage + 5)

        self.events.add_event(job.job_id, "agent_material_parser_started", "agent_material_parser_started", "Material parser agent started (dry-run).")
        job = self._progress(job, stage := stage + 3)
        self.events.add_event(job.job_id, "agent_fact_extractor_started", "agent_fact_extractor_started", "Fact extractor agent started (dry-run).")
        job = self._progress(job, stage := stage + 3)

        self.events.add_event(job.job_id, "retrieval_boundary_checked", "retrieval_boundary_checked", "BGE-M3 partly_effective; reranker diagnostic_only.")
        job = self._progress(job, stage := stage + 3)
        self.events.add_event(job.job_id, "agent_compliance_analyzer_started", "agent_compliance_analyzer_started", "Compliance analyzer agent started (dry-run).")
        job = self._progress(job, stage := stage + 3)

        self.events.add_event(job.job_id, "risk_points_identified", "risk_points_identified", "Risk points identified.", {"risk_points": intake.missing_information})
        job = self._progress(job, stage := stage + 3)

        self.events.add_event(job.job_id, "prototype_report_started", "prototype_report_started", "Generating prototype diagnostic report.")
        job = self._progress(job, stage := stage + 3)

        advice = self.advice_service.generate(req.assessment_type, req.user_prompt, intake, intent)
        artifacts = self._write_enhanced_dry_artifacts(job, req, previews, intake, intent, advice)
        self.events.add_event(job.job_id, "prototype_report_completed", "prototype_report_completed", "Prototype diagnostic report completed.", {"artifacts": artifacts})
        job = self._progress(job, stage := stage + 5)

        self.events.add_event(job.job_id, "artifact_collection_completed", "artifact_collection_completed", "All artifacts collected into runtime_storage.")
        job = self._progress(job, 100)

        job = job.model_copy(
            update={
                "status": JobStatus.completed,
                "completed_at": utc_now(),
                "current_stage": "completed",
                "result_artifacts": artifacts,
            }
        )
        self._save_job(job)
        self.events.add_event(job.job_id, "final", "completed", "Final event: job completed. This is a prototype diagnostic, not formal legal opinion.")
        return job

    def _fail_controlled_runtime(self, job: RuntimeJob) -> RuntimeJob:
        self.events.add_event(job.job_id, "job_created", "job_created", "Controlled runtime job created.")
        self.events.add_event(
            job.job_id,
            "runtime_adapter_not_configured",
            "failed",
            "Controlled runtime is disabled or not configured; no real runtime was executed.",
            self.adapter.plan(RuntimeMode.controlled_runtime),
        )
        job = job.model_copy(
            update={
                "status": JobStatus.failed,
                "started_at": utc_now(),
                "completed_at": utc_now(),
                "progress": 100,
                "current_stage": "failed",
                "error_message": "runtime_adapter_not_configured",
            }
        )
        self._save_job(job)
        self.events.add_event(job.job_id, "final", "failed", "Final event: job failed.")
        return job

    def _run_uploaded_material_job(self, job: RuntimeJob, req: RunAssessmentRequest) -> RuntimeJob:
        job = job.model_copy(update={"status": JobStatus.running, "started_at": utc_now(), "progress": 1, "current_stage": "job_created"})
        self._save_job(job)
        self.events.add_event(job.job_id, "job_created", "job_created", "Uploaded material runtime job created.", self.adapter.plan(req.runtime_mode))

        stage = 5
        self.events.add_event(job.job_id, "user_prompt_received", "user_prompt_received", "User prompt received.", {"prompt_length": len(req.user_prompt)})
        job = self._progress(job, stage := stage + 5)

        self.events.add_event(job.job_id, "uploaded_materials_loaded", "uploaded_materials_loaded", "Uploaded materials loaded for dynamic runtime.")
        job = self._progress(job, stage := stage + 5)

        file_records = [self.files.get_file(file_id) for file_id in req.file_ids]
        valid_files = [item for item in file_records if item is not None]
        previews = [
            {"file_id": item.file_id, "display_path": item.display_path, "parse_status": item.parse_status}
            for item in valid_files
        ]

        intake = self.intake_service.intake(valid_files, req.user_prompt)
        job = self._progress(job, stage := stage + 5)

        try:
            artifacts = self.orchestrator.run(
                job, job.conversation_id, req.user_prompt,
                str(req.assessment_type), req.file_ids, valid_files, intake,
            )
            job = job.model_copy(
                update={
                    "status": JobStatus.completed,
                    "completed_at": utc_now(),
                    "progress": 100,
                    "current_stage": "completed",
                    "result_artifacts": artifacts,
                }
            )
            self._save_job(job)
            self.memory.record_job_summary(job, artifacts)
            return job
        except Exception as exc:
            error_type = "uploaded_material_runtime_failed"
            self.events.add_event(job.job_id, "runtime_failed", "failed", f"Uploaded material runtime failed: {type(exc).__name__}: {exc}")
            self.events.add_event(job.job_id, "final", "failed", "Final event: job failed.")
            artifacts = self._write_runtime_failure_artifacts(job, req, previews, f"{type(exc).__name__}: {exc}", error_type)
            job = job.model_copy(
                update={
                    "status": JobStatus.failed,
                    "completed_at": utc_now(),
                    "progress": 100,
                    "current_stage": "failed",
                    "error_message": error_type,
                    "result_artifacts": artifacts,
                }
            )
            self._save_job(job)
            self.memory.record_job_summary(job, artifacts)
            return job

    def _run_full_chain_job(self, job: RuntimeJob, req: RunAssessmentRequest) -> RuntimeJob:
        job = job.model_copy(update={"status": JobStatus.running, "started_at": utc_now(), "progress": 1, "current_stage": "job_created"})
        self._save_job(job)
        self.events.add_event(job.job_id, "job_created", "job_created", "Full-chain runtime job created.", self.adapter.plan(req.runtime_mode))

        stage = 5
        self.events.add_event(job.job_id, "user_prompt_received", "user_prompt_received", "User prompt received.", {"prompt_length": len(req.user_prompt)})
        job = self._progress(job, stage := stage + 5)

        self.events.add_event(job.job_id, "uploaded_materials_loaded", "uploaded_materials_loaded", "Uploaded materials loaded for full-chain runtime.")
        job = self._progress(job, stage := stage + 5)

        file_records = [self.files.get_file(file_id) for file_id in req.file_ids]
        valid_files = [item for item in file_records if item is not None]
        previews = [
            {"file_id": item.file_id, "display_path": item.display_path, "parse_status": item.parse_status}
            for item in valid_files
        ]

        intake = self.intake_service.intake(valid_files, req.user_prompt)
        job = self._progress(job, stage := stage + 5)

        try:
            artifacts = self.full_chain_orchestrator.run(
                job, job.conversation_id, req.user_prompt,
                str(req.assessment_type), req.file_ids, valid_files, intake,
            )
            job = job.model_copy(
                update={
                    "status": JobStatus.completed,
                    "completed_at": utc_now(),
                    "progress": 100,
                    "current_stage": "completed",
                    "result_artifacts": artifacts,
                }
            )
            self._save_job(job)
            return job
        except Exception as exc:
            error_type = "full_chain_runtime_failed"
            self.events.add_event(job.job_id, "runtime_failed", "failed", f"Full-chain runtime failed: {type(exc).__name__}: {exc}")
            self.events.add_event(job.job_id, "final", "failed", "Final event: job failed.")
            artifacts = self._write_runtime_failure_artifacts(job, req, previews, f"{type(exc).__name__}: {exc}", error_type)
            job = job.model_copy(
                update={
                    "status": JobStatus.failed,
                    "completed_at": utc_now(),
                    "progress": 100,
                    "current_stage": "failed",
                    "error_message": error_type,
                    "result_artifacts": artifacts,
                }
            )
            self._save_job(job)
            return job

    def _run_controlled_job(self, job: RuntimeJob, req: RunAssessmentRequest) -> RuntimeJob:
        job = job.model_copy(update={"status": JobStatus.running, "started_at": utc_now(), "progress": 10, "current_stage": "runtime_adapter_started"})
        self._save_job(job)
        self.events.add_event(job.job_id, "runtime_adapter_started", "runtime_adapter_started", "Controlled runtime adapter started.", self.adapter.plan(req.runtime_mode))
        self.events.add_event(job.job_id, "runtime_contract_discovered", "runtime_contract_discovered", "Preset 18-case runtime contract discovered.")
        file_records = [self.files.get_file(file_id) for file_id in req.file_ids]
        previews = [
            {
                "file_id": item.file_id,
                "display_path": item.display_path,
                "parse_status": item.parse_status,
                "uploaded_material_usage": "preview_only",
            }
            for item in file_records
            if item is not None
        ]
        self.events.add_event(job.job_id, "input_materials_loaded", "input_materials_loaded", "Uploaded materials loaded as preview_only/intake_only.", {"files": previews})
        self.events.add_event(job.job_id, "assessment_context_built", "assessment_context_built", "Assessment context built without database ingestion.", {"assessment_type": req.assessment_type})
        case_id = self.adapter.select_case_id(req.user_prompt)
        self.events.add_event(job.job_id, "case_mapping_attempted", "case_mapping_attempted", "Mapped prompt to preset controlled case.", {"case_id": case_id})
        self.events.add_event(job.job_id, "core_runtime_started", "core_runtime_started", "Calling core/v12 structured preflight case runtime.")
        try:
            artifacts = self.adapter.run_controlled_case_runtime(
                job.job_id,
                req.user_prompt,
                previews,
                str(req.assessment_type),
                storage=self.storage,
            )
            self.events.add_event(job.job_id, "artifact_collection_started", "artifact_collection_started", "Runtime artifacts collected into runtime_storage.", {"artifacts": artifacts})
            job = job.model_copy(
                update={
                    "status": JobStatus.completed,
                    "completed_at": utc_now(),
                    "progress": 100,
                    "current_stage": "completed",
                    "result_artifacts": artifacts,
                }
            )
            self._save_job(job)
            self.events.add_event(job.job_id, "runtime_completed", "completed", "Controlled case runtime completed.")
            self.events.add_event(job.job_id, "final", "completed", "Final event: job completed.")
            return job
        except Exception as exc:
            error_type = "runtime_contract_not_supported" if "not_supported" in str(exc) else "controlled_case_runtime_failed"
            self.events.add_event(job.job_id, error_type, "failed", f"Controlled runtime failed: {type(exc).__name__}: {exc}")
            artifacts = self._write_runtime_failure_artifacts(job, req, previews, f"{type(exc).__name__}: {exc}", error_type)
            job = job.model_copy(
                update={
                    "status": JobStatus.failed,
                    "completed_at": utc_now(),
                    "progress": 100,
                    "current_stage": "failed",
                    "error_message": error_type,
                    "result_artifacts": artifacts,
                }
            )
            self._save_job(job)
            self.events.add_event(job.job_id, "final", "failed", "Final event: job failed.")
            return job

    def _write_enhanced_dry_artifacts(
        self,
        job: RuntimeJob,
        req: RunAssessmentRequest,
        previews: List[dict],
        intake: Any,
        intent: Any,
        advice: Any,
    ) -> Dict[str, str]:
        artifacts_dir = self.storage.artifacts_dir(job.job_id)
        artifacts = {
            "runtime_result.json": {
                "job_id": job.job_id,
                "status": "completed",
                "mode": "dry_run",
                "not_formal_legal_opinion": True,
                "source_backed": False,
                "manual_verified": False,
                "article_level_verified": False,
                "uploaded_files_written_to_chroma": False,
                "uploaded_files_written_to_neo4j": False,
            },
            "uploaded_material_intake.json": intake.model_dump(mode="json"),
            "assessment_intent.json": intent.model_dump(mode="json"),
            "prototype_compliance_suggestions.json": advice.model_dump(mode="json"),
            "evidence_pack.json": {
                "evidence_rows": [],
                "source_backed": False,
                "manual_verified": False,
                "article_level_verified": False,
                "needs_manual_verification": True,
                "file_previews": previews,
            },
            "citation_plan.json": {"citations": [], "diagnostic_only": True},
            "score.json": {
                "final_score": None,
                "programmatic_score": None,
                "llm_score": None,
                "cap_reason": "dry_run_placeholder_no_real_assessment",
            },
        }
        report_lines = [
            "# Prototype Diagnostic Report",
            "",
            "> This is a prototype diagnostic artifact, not formal legal advice.",
            f"> assessment_type: {req.assessment_type}",
            "> source_backed: false",
            "> manual_verified: false",
            "> article_level_verified: false",
            "> Chroma/Neo4j/current_backend were not modified.",
            "",
            f"## User Prompt",
            req.user_prompt,
            "",
            f"## Assessment Type",
            str(req.assessment_type),
            "",
            f"## Uploaded Files",
            f"Count: {len(previews)}",
        ]
        for p in previews:
            report_lines.append(f"- `{p.get('file_path', p.get('display_path', 'unknown'))}` ({p.get('parse_status', 'unknown')})")

        report_lines.append("")
        report_lines.append("## Uploaded Material Intake")
        for key in ("parties", "data_type", "transfer_direction", "cross_border_indicators", "personal_information_indicators", "sensitive_pi_indicators", "transaction_context"):
            val = getattr(intake, key, [])
            if val:
                report_lines.append(f"- **{key}**: {', '.join(val)}")

        report_lines.append("")
        report_lines.append("## Detected Risks")
        for risk in getattr(intake, "missing_information", []):
            report_lines.append(f"- {risk}")

        report_lines.append("")
        report_lines.append("## Prototype Compliance Suggestions")
        for issue in getattr(advice, "identified_issues", []):
            report_lines.append(f"- {issue}")

        report_lines.append("")
        report_lines.append("## Suggested Next Steps")
        for supp in getattr(advice, "suggested_supplements", []):
            report_lines.append(f"- {supp}")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append(f"*Generated at {utc_now()} - Prototype Diagnostic Only*")

        report = "\n".join(report_lines)

        rel_paths: Dict[str, str] = {}
        for name, data in artifacts.items():
            path = artifacts_dir / name
            write_json_atomic(path, data)
            rel_paths[name] = self.storage.display_path(path)
        report_path = artifacts_dir / "prototype_report.md"
        report_path.write_text(report, encoding="utf-8")
        rel_paths["prototype_report.md"] = self.storage.display_path(report_path)
        return rel_paths

    def _progress(self, job: RuntimeJob, value: int) -> RuntimeJob:
        updated = job.model_copy(update={"progress": min(value, 99)})
        self._save_job(updated)
        return updated

    def _write_runtime_failure_artifacts(
        self,
        job: RuntimeJob,
        req: RunAssessmentRequest,
        previews: List[dict],
        error_message: str,
        error_type: str,
    ) -> Dict[str, str]:
        artifacts_dir = self.storage.artifacts_dir(job.job_id)
        payloads = {
            "runtime_manifest.json": {
                "runtime_mode": "runtime_failed",
                "error_type": error_type,
                "error_message": error_message,
                "controlled_case_runtime_supported": True,
                "uploaded_material_runtime_supported": False,
                "uploaded_material_usage": "preview_only",
                "source_backed_claim_fabricated": False,
                "manual_verified_claim_fabricated": False,
                "article_level_verified_claim_fabricated": False,
            },
            "input_materials_manifest.json": {
                "user_prompt": req.user_prompt,
                "file_previews": previews,
                "uploaded_material_usage": "preview_only",
            },
            "missing_artifacts.json": {
                "missing_artifacts": [
                    "runtime_result.json",
                    "report.md",
                    "evidence_pack.json",
                    "citation_plan.json",
                    "source_trace.json",
                    "retrieval_trace.json",
                    "score.json",
                ],
                "reason": error_type,
            },
        }
        rel_paths: Dict[str, str] = {}
        for name, data in payloads.items():
            path = artifacts_dir / name
            write_json_atomic(path, data)
            rel_paths[name] = self.storage.display_path(path)
        return rel_paths

    def _save_job(self, job: RuntimeJob) -> None:
        write_json_atomic(self.storage.job_json(job.job_id), job.model_dump(mode="json"))
