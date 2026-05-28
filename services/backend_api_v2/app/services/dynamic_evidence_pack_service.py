from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    evidence_id: str = ""
    claim_id: str = ""
    source_id: str = ""
    chunk_id: str = ""
    local_path: str = ""
    collection: str = ""
    evidence_type: str = ""
    content: str = ""
    support_strength: str = "none"
    source_backed: bool = False
    needs_manual_verification: bool = True


class EvidencePackResult(BaseModel):
    total_evidence: int = 0
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    source_backed: bool = False
    manual_verified: bool = False
    article_level_verified: bool = False
    insufficient_evidence: bool = True
    fallback_used: bool = True
    source: str = "rules_based"


class DynamicEvidencePackService:
    def build(self, claims: List[Dict[str, Any]], retrieval_trace: Any,
              extracted_facts: Any) -> EvidencePackResult:
        evidence_items: List[EvidenceItem] = []

        if retrieval_trace and hasattr(retrieval_trace, "items"):
            for item in retrieval_trace.items:
                for claim in claims:
                    evidence_items.append(EvidenceItem(
                        evidence_id=f"EV-{len(evidence_items)+1:04d}",
                        claim_id=claim.get("claim_id", ""),
                        source_id=item.source_id if hasattr(item, 'source_id') else "",
                        chunk_id=item.chunk_id if hasattr(item, 'chunk_id') else "",
                        local_path=item.local_path if hasattr(item, 'local_path') else "",
                        collection=item.collection if hasattr(item, 'collection') else "",
                        evidence_type="legal_basis",
                        content=f"来源: {item.source_id if hasattr(item, 'source_id') else 'fallback'}",
                        support_strength="low",
                        source_backed=not (item.fallback_used if hasattr(item, 'fallback_used') else True),
                        needs_manual_verification=True,
                    ))

        if extracted_facts and hasattr(extracted_facts, "evidence_from_uploaded_material"):
            mat_evidence = extracted_facts.evidence_from_uploaded_material or []
            for idx, ev in enumerate(mat_evidence[:20]):
                evidence_items.append(EvidenceItem(
                    evidence_id=f"EV-MAT-{idx+1:04d}",
                    claim_id="material_facts",
                    source_id="uploaded_material",
                    chunk_id=f"uploaded_{idx}",
                    evidence_type="business_fact",
                    content=str(ev)[:500],
                    support_strength="low",
                    source_backed=False,
                    needs_manual_verification=True,
                ))

        return EvidencePackResult(
            total_evidence=len(evidence_items),
            evidence_items=evidence_items,
            source_backed=any(e.source_backed for e in evidence_items),
            manual_verified=False,
            article_level_verified=False,
            insufficient_evidence=len(evidence_items) < 3,
            fallback_used=all(not e.source_backed for e in evidence_items) if evidence_items else True,
            source="retrieval_based" if evidence_items else "rules_based",
        )

    def build_from_bridge(self, bridge_evidence_pack: Any) -> EvidencePackResult:
        evidence_items: List[EvidenceItem] = []
        if isinstance(bridge_evidence_pack, dict):
            rows = bridge_evidence_pack.get("evidence_rows", bridge_evidence_pack.get("rows", []))
            for row in rows:
                evidence_items.append(EvidenceItem(
                    evidence_id=str(row.get("evidence_id", "")),
                    claim_id=str(row.get("claim_id", "")),
                    source_id=str(row.get("source_id", "")),
                    chunk_id=str(row.get("chunk_id", "")),
                    evidence_type=str(row.get("evidence_role", "legal_basis")),
                    content=str(row.get("claim_binding", ""))[:500],
                ))
        return EvidencePackResult(
            total_evidence=len(evidence_items),
            evidence_items=evidence_items,
            source_backed=True,
            insufficient_evidence=len(evidence_items) == 0,
            fallback_used=False,
            source="core_v12_bridge",
        )
