from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class CitationItem(BaseModel):
    citation_id: str = ""
    evidence_id: str = ""
    source_id: str = ""
    chunk_id: str = ""
    local_path: str = ""
    collection: str = ""
    law_reference: str = ""
    article_reference: str = ""
    content: str = ""
    verified: bool = False
    diagnostic_only: bool = True


class CitationPlanResult(BaseModel):
    total_citations: int = 0
    citations: List[CitationItem] = Field(default_factory=list)
    diagnostic_only: bool = True
    fallback_used: bool = True
    source: str = "rules_based"


class DynamicCitationPlanService:
    def build(self, claims: List[Dict[str, Any]], evidence_items: List[Any],
              retrieval_trace: Any = None) -> CitationPlanResult:
        citations: List[CitationItem] = []

        if retrieval_trace and hasattr(retrieval_trace, "items"):
            for idx, item in enumerate(retrieval_trace.items):
                si = item.source_id if hasattr(item, 'source_id') else ""
                ci = item.chunk_id if hasattr(item, 'chunk_id') else ""
                lp = item.local_path if hasattr(item, 'local_path') else ""
                col = item.collection if hasattr(item, 'collection') else ""
                citations.append(CitationItem(
                    citation_id=f"CIT-{idx+1:04d}",
                    evidence_id=f"EV-{idx+1:04d}",
                    source_id=str(si),
                    chunk_id=str(ci),
                    local_path=str(lp),
                    collection=str(col),
                    law_reference=str(si) if si else "fallback_reference",
                    article_reference=str(ci),
                    content=f"引用自: {si}" if si else "规则型引用",
                    verified=False,
                    diagnostic_only=True,
                ))

        if not citations:
            for idx, claim in enumerate(claims[:10]):
                law = claim.get("law", "")
                citations.append(CitationItem(
                    citation_id=f"CIT-FB-{idx+1:04d}",
                    evidence_id=f"EV-FB-{idx+1:04d}",
                    source_id="fallback",
                    chunk_id=f"fallback_{idx}",
                    law_reference=law,
                    article_reference="规则型匹配",
                    content=f"规则型引用: {law} - {claim.get('title', '')}",
                    verified=False,
                    diagnostic_only=True,
                ))

        return CitationPlanResult(
            total_citations=len(citations),
            citations=citations,
            diagnostic_only=True,
            fallback_used=not bool(retrieval_trace and getattr(retrieval_trace, "real_legal_retrieval_used", False)),
            source="retrieval_based" if bool(retrieval_trace and getattr(retrieval_trace, "real_legal_retrieval_used", False)) else "rules_based",
        )

    def build_from_bridge(self, bridge_citations: List[Any]) -> CitationPlanResult:
        citations: List[CitationItem] = []
        for idx, c in enumerate(bridge_citations):
            cd = c.to_row() if hasattr(c, 'to_row') else (c.__dict__ if hasattr(c, '__dict__') else c)
            if isinstance(cd, dict):
                citations.append(CitationItem(
                    citation_id=cd.get("citation_id", f"CIT-{idx+1:04d}"),
                    evidence_id=cd.get("evidence_id", ""),
                    source_id=cd.get("source_id", ""),
                    chunk_id=cd.get("chunk_id", ""),
                    law_reference=cd.get("law_reference", cd.get("source_id", "")),
                    article_reference=cd.get("article_id", cd.get("chunk_id", "")),
                    content=cd.get("citation_text", "")[:500],
                    verified=False,
                    diagnostic_only=True,
                ))
        return CitationPlanResult(
            total_citations=len(citations),
            citations=citations,
            diagnostic_only=True,
            fallback_used=False,
            source="core_v12_bridge",
        )
