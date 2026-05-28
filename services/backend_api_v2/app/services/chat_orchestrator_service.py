from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.boundaries import BOUNDARY_FLAGS
from app.models.assessment import AssessmentType
from app.models.chat import CreateMessageRequest, MessageRole
from app.models.job import RunAssessmentRequest, RuntimeMode
from app.services.assessment_intent_service import AssessmentIntent, AssessmentIntentService
from app.services.chat_intent_router import ChatIntentRouter
from app.services.conversation_service import ConversationService
from app.services.conversational_rag_service import ConversationalRAGService
from app.services.file_upload_service import FileUploadService
from app.services.llm_chat_service import LLMChatService
from app.services.prototype_advice_service import PrototypeAdvice, PrototypeAdviceService
from app.services.runtime_job_service import RuntimeJobService
from app.services.uploaded_material_intake_service import UploadedMaterialIntake, UploadedMaterialIntakeService


class ChatRequest(BaseModel):
    content: str = ""
    message: Optional[str] = None
    assessment_type: Optional[AssessmentType] = None
    file_ids: List[str] = Field(default_factory=list)
    auto_run_assessment: bool = False
    runtime_mode: RuntimeMode = RuntimeMode.dry_run
    action: str = "send_message"
    rag_enabled: bool = True
    autojudge_enabled: bool = True


class ChatResponse(BaseModel):
    user_message: Dict[str, Any]
    assistant_message: Dict[str, Any]
    intent: Dict[str, Any]
    uploaded_material_intake: Dict[str, Any]
    suggested_next_actions: List[str] = Field(default_factory=list)
    job_id: Optional[str] = None
    runtime_mode_effective: str = "dry_run"
    auto_judge_expected: bool = False
    full_chain_runtime_supported: bool = True
    runtime_limitations: List[str] = Field(default_factory=list)
    recommended_followups: List[str] = Field(default_factory=list)
    boundary_flags: Dict[str, Any] = Field(default_factory=dict)
    chat_metadata: Dict[str, Any] = Field(default_factory=dict)
    full_chain_job_created: bool = False
    report_generated: bool = False
    rag_used: bool = False
    llm_used: bool = False
    uploaded_file_context_used: bool = False


class ChatOrchestratorService:
    def __init__(self) -> None:
        self.conversations = ConversationService()
        self.files = FileUploadService()
        self.intent_service = AssessmentIntentService()
        self.chat_intent_router = ChatIntentRouter()
        self.intake_service = UploadedMaterialIntakeService()
        self.advice_service = PrototypeAdviceService()
        self.llm_chat = LLMChatService()
        self.conversational_rag = ConversationalRAGService()
        self.job_service = RuntimeJobService()

    def chat(self, conversation_id: str, req: ChatRequest) -> ChatResponse:
        self.conversations.require_conversation(conversation_id)
        content = (req.message or req.content or "").strip()
        if not content:
            content = "请说明你的问题或评估需求。"

        user_message = self.conversations.add_message(
            conversation_id,
            CreateMessageRequest(content=content, attachments=req.file_ids),
            role=MessageRole.user,
        )

        file_records = [self.files.get_file(file_id) for file_id in req.file_ids]
        valid_files = [item for item in file_records if item is not None and item.conversation_id == conversation_id]

        assessment_type = req.assessment_type or AssessmentType.general_data_compliance_diagnostic

        intent = self.intent_service.detect(content, req.assessment_type)
        if not req.assessment_type and intent.detected_type != AssessmentType.general_data_compliance_diagnostic:
            assessment_type = intent.detected_type

        intake = self.intake_service.intake(valid_files, content)

        action = req.action or ("run_full_chain_report" if req.auto_run_assessment else "send_message")
        if action == "run_full_chain_report" or req.auto_run_assessment:
            req = req.model_copy(update={"autojudge_enabled": True})
            return self._run_full_chain_report(
                conversation_id=conversation_id,
                req=req,
                content=content,
                user_message=user_message.model_dump(mode="json"),
                assessment_type=assessment_type,
                intent=intent,
                intake=intake,
                valid_files=valid_files,
            )

        req = req.model_copy(update={"autojudge_enabled": False})
        return self._send_chat_message(
            conversation_id=conversation_id,
            content=content,
            user_message=user_message.model_dump(mode="json"),
            assessment_type=assessment_type,
            intent=intent,
            intake=intake,
            valid_files=valid_files,
            req=req,
        )

    def _send_chat_message(
        self,
        *,
        conversation_id: str,
        content: str,
        user_message: Dict[str, Any],
        assessment_type: AssessmentType,
        intent: AssessmentIntent,
        intake: UploadedMaterialIntake,
        valid_files: List[Any],
        req: ChatRequest,
    ) -> ChatResponse:
        chat_intent = self.chat_intent_router.detect(content, req.file_ids)
        rag_result: Dict[str, Any] = {
            "rag_used": False,
            "real_legal_retrieval_used": False,
            "retrieval_fallback_used": False,
            "fallback_reason": "",
            "context_items": [],
        }
        if self.conversational_rag.should_retrieve(content, chat_intent, req.rag_enabled):
            rag_result = self.conversational_rag.retrieve(content, str(assessment_type))

        uploaded_context = [
            {
                "file_id": item.file_id,
                "original_filename": item.original_filename,
                "parse_status": item.parse_status,
                "text_preview": item.text_preview or "",
            }
            for item in valid_files
        ]
        llm_result = self.llm_chat.complete(
            user_message=content,
            intent=chat_intent,
            rag_context=rag_result.get("context_items") or [],
            uploaded_context=uploaded_context,
        )
        assistant_content = self._decorate_chat_answer(
            llm_result.get("content", ""),
            rag_result,
            uploaded_context_used=bool(uploaded_context),
        )

        assistant_message = self.conversations.add_message(
            conversation_id,
            CreateMessageRequest(content=assistant_content, attachments=[]),
            role=MessageRole.assistant,
        )

        metadata = {
            "chat_mode": "conversational_rag",
            "action": "send_message",
            "intent": chat_intent,
            "llm_used": bool(llm_result.get("llm_used")),
            "llm_unavailable": bool(llm_result.get("llm_unavailable")),
            "rag_used": bool(rag_result.get("rag_used")),
            "real_legal_retrieval_used": bool(rag_result.get("real_legal_retrieval_used")),
            "retrieval_fallback_used": bool(rag_result.get("retrieval_fallback_used")),
            "uploaded_file_context_used": bool(uploaded_context),
            "full_chain_job_created": False,
            "report_generated": False,
            "boundary": "uploaded_materials_business_facts_only_not_legal_basis",
            "llm_config": llm_result.get("llm_config", {}),
        }

        return ChatResponse(
            user_message=user_message,
            assistant_message=assistant_message.model_dump(mode="json"),
            intent=intent.model_dump(mode="json"),
            uploaded_material_intake=intake.model_dump(mode="json"),
            suggested_next_actions=[
                "send_message: 可继续普通问答，不会生成报告",
                "run_full_chain_report: 上传材料后点击「生成审查报告」启动多智能体链路",
            ],
            job_id=None,
            runtime_mode_effective="chat",
            auto_judge_expected=False,
            full_chain_runtime_supported=True,
            runtime_limitations=[],
            recommended_followups=[],
            boundary_flags=BOUNDARY_FLAGS,
            chat_metadata=metadata,
            full_chain_job_created=False,
            report_generated=False,
            rag_used=metadata["rag_used"],
            llm_used=metadata["llm_used"],
            uploaded_file_context_used=metadata["uploaded_file_context_used"],
        )

    def _run_full_chain_report(
        self,
        *,
        conversation_id: str,
        req: ChatRequest,
        content: str,
        user_message: Dict[str, Any],
        assessment_type: AssessmentType,
        intent: AssessmentIntent,
        intake: UploadedMaterialIntake,
        valid_files: List[Any],
    ) -> ChatResponse:
        if not req.file_ids or not valid_files:
            assistant_content = (
                "请先上传业务材料，例如合同、数据说明、隐私政策或处理活动说明，再点击「生成审查报告」。\n\n"
                "本次未创建审查任务，也未生成报告。上传材料只会作为业务事实材料，不会写入法规库、图数据库、向量库或后端指针文件。"
            )
            assistant_message = self.conversations.add_message(
                conversation_id,
                CreateMessageRequest(content=assistant_content, attachments=[]),
                role=MessageRole.assistant,
            )
            return ChatResponse(
                user_message=user_message,
                assistant_message=assistant_message.model_dump(mode="json"),
                intent=intent.model_dump(mode="json"),
                uploaded_material_intake=intake.model_dump(mode="json"),
                suggested_next_actions=["先上传业务材料", "上传后再生成审查报告"],
                job_id=None,
                runtime_mode_effective="full_chain_runtime",
                auto_judge_expected=False,
                full_chain_runtime_supported=True,
                runtime_limitations=["file_ids_empty_or_not_owned_by_conversation"],
                recommended_followups=[],
                boundary_flags=BOUNDARY_FLAGS,
                chat_metadata={
                    "chat_mode": "report_request_blocked",
                    "action": "run_full_chain_report",
                    "full_chain_job_created": False,
                    "report_generated": False,
                    "file_ids_non_empty": False,
                },
                full_chain_job_created=False,
                report_generated=False,
            )

        interim = self.conversations.add_message(
            conversation_id,
            CreateMessageRequest(
                content="已收到材料，正在启动合规审查。右侧审查面板将展示进度、证据、人工复核状态和报告下载。",
                attachments=[],
            ),
            role=MessageRole.assistant,
        )

        run_req = RunAssessmentRequest(
            assessment_type=assessment_type,
            user_prompt=content,
            file_ids=[item.file_id for item in valid_files],
            runtime_mode=RuntimeMode.full_chain_runtime,
            action="run_full_chain_report",
            autojudge_enabled=True,
        )
        job = self.job_service.create_async(conversation_id, run_req)
        final_content = (
            "审查报告生成已开始。右侧审查面板将展示审查进度、证据与引用、人工复核状态和报告下载。\n\n"
            "- 上传材料仅作为业务事实，法律依据只来自只读合规知识库和引用证据。\n"
            "- 当前输出为非正式合规辅助分析，不构成正式法律意见。"
        )
        final_message = self.conversations.add_message(
            conversation_id,
            CreateMessageRequest(content=final_content, attachments=[]),
            role=MessageRole.assistant,
        )

        return ChatResponse(
            user_message=user_message,
            assistant_message=final_message.model_dump(mode="json"),
            intent=intent.model_dump(mode="json"),
            uploaded_material_intake=intake.model_dump(mode="json"),
            suggested_next_actions=["查看审查进度", "查看证据与引用", "下载报告"],
            job_id=job.job_id,
            runtime_mode_effective=RuntimeMode.full_chain_runtime.value,
            auto_judge_expected=True,
            full_chain_runtime_supported=True,
            runtime_limitations=[],
            recommended_followups=[],
            boundary_flags=BOUNDARY_FLAGS,
            chat_metadata={
                "chat_mode": "full_chain_report",
                "action": "run_full_chain_report",
                "interim_message_id": interim.message_id,
                "full_chain_job_created": True,
                "report_generated": False,
                "file_ids_non_empty": True,
                "async_job": True,
                "not_production_queue": True,
            },
            full_chain_job_created=True,
            report_generated=False,
            rag_used=True,
            llm_used=False,
            uploaded_file_context_used=True,
        )

    def _decorate_chat_answer(self, answer: str, rag_result: Dict[str, Any], uploaded_context_used: bool) -> str:
        notes: List[str] = []
        if rag_result.get("rag_used"):
            if rag_result.get("real_legal_retrieval_used"):
                notes.append("本次回答参考了只读法规/RAG 检索摘要。")
            else:
                notes.append(
                    f"本次尝试了只读法规/RAG 检索，但未形成真实法规命中；状态：{rag_result.get('fallback_reason') or 'fallback'}。"
                )
        if uploaded_context_used:
            notes.append("上传材料仅用于业务事实摘要，不作为法律依据。")
        notes.append("以上为非正式合规辅助分析，不构成正式法律意见。")
        return answer.strip() + "\n\n---\n" + "\n".join(f"- {note}" for note in notes)

    def _build_report_final_summary(self, job_id: str) -> str:
        try:
            artifacts = self.job_service.artifacts(job_id).get("artifacts", {})
            import json

            def load(name: str) -> Dict[str, Any]:
                value = artifacts.get(name)
                if isinstance(value, str) and value.strip().startswith("{"):
                    return json.loads(value)
                return value if isinstance(value, dict) else {}

            risk = load("risk_score.json")
            quality = load("quality_gate.json")
            missing = load("missing_capabilities.json")
            risk_level = risk.get("overall_risk_level", "unknown")
            gate = quality.get("gate_status", "unknown")
            missing_items = missing.get("missing_capabilities", missing.get("items", []))
            return (
                "审查报告已生成。右侧合规审查工作区可查看审查进度、证据与引用、人工复核状态和报告下载。\n\n"
                f"- 风险等级：{risk_level}\n"
                f"- 审查状态：{gate}\n"
                f"- 待补充证据：{len(missing_items) if isinstance(missing_items, list) else '需查看证据整理'}\n\n"
                "本报告为非正式合规辅助分析，不构成正式法律意见。上传材料仅作为业务事实，法律依据来自只读合规知识库。"
            )
        except Exception:
            return (
                "合规审查任务已完成或进入终态。请在右侧合规审查工作区查看报告、证据、引用与人工复核状态。"
                "本内容不构成正式法律意见。"
            )
