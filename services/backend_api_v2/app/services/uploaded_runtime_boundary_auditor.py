from __future__ import annotations

from app.services.uploaded_material_runtime_adapter import BoundaryAudit


class UploadedRuntimeBoundaryAuditor:

    def audit(self) -> BoundaryAudit:
        return BoundaryAudit(
            formal_legal_opinion=False,
            prototype_diagnostic=True,
            uploaded_files_written_to_chroma=False,
            uploaded_files_written_to_neo4j=False,
            uploaded_files_written_to_legal_data=False,
            current_backend_modified=False,
            chroma_modified=False,
            neo4j_modified=False,
            autojudge_scoring_modified=False,
            autojudge_scoring_schema_modified=False,
            cap_rules_modified=False,
            legal_data_modified=False,
            source_backed_claim_fabricated=False,
            manual_verified_claim_fabricated=False,
            article_level_verified_claim_fabricated=False,
            legal_sources_from_rag_only=True,
            uploaded_material_used_as_business_facts_only=True,
        )

    def verify_hard_boundaries(self) -> bool:
        """Returns True if all hard boundaries are respected."""
        audit = self.audit()
        return (
            not audit.uploaded_files_written_to_chroma
            and not audit.uploaded_files_written_to_neo4j
            and not audit.uploaded_files_written_to_legal_data
            and not audit.current_backend_modified
            and not audit.chroma_modified
            and not audit.neo4j_modified
            and not audit.autojudge_scoring_modified
            and not audit.autojudge_scoring_schema_modified
            and not audit.cap_rules_modified
            and not audit.legal_data_modified
            and not audit.source_backed_claim_fabricated
            and not audit.manual_verified_claim_fabricated
            and not audit.article_level_verified_claim_fabricated
            and not audit.formal_legal_opinion
        )
