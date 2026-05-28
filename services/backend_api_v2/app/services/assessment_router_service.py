from __future__ import annotations

from app.models.assessment import ASSESSMENT_DESCRIPTIONS, AssessmentType, AssessmentTypeInfo


class AssessmentRouterService:
    def list_types(self) -> list[AssessmentTypeInfo]:
        return [
            AssessmentTypeInfo(
                assessment_type=assessment_type,
                label=label,
                description=f"{label}；diagnostic prototype only, not formal legal opinion.",
            )
            for assessment_type, label in ASSESSMENT_DESCRIPTIONS.items()
        ]

    def build_prompt(self, assessment_type: AssessmentType, user_prompt: str) -> str:
        label = ASSESSMENT_DESCRIPTIONS[assessment_type]
        return (
            f"Assessment type: {assessment_type}\n"
            f"Label: {label}\n"
            "Boundary: prototype diagnostic only; do not claim source-backed, manual verified, or article-level verified.\n"
            f"User prompt: {user_prompt}"
        )
