from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RetrievalTraceItem(BaseModel):
    query: str = ""
    collection: str = ""
    source_id: str = ""
    chunk_id: str = ""
    local_path: str = ""
    evidence_role: str = ""
    score: float = 0.0
    retrieval_mode: str = "fallback"
    fallback_used: bool = True
    claim_id: str = ""
    claim_title: str = ""


class RetrievalTrace(BaseModel):
    retrieval_attempted: bool = False
    retrieval_successful: bool = False
    real_legal_retrieval_used: bool = False
    retrieval_fallback_used: bool = True
    queries: List[str] = Field(default_factory=list)
    backend_type: str = "unknown"
    embedding_model: str = "unknown"
    collections_queried: List[str] = Field(default_factory=list)
    items: List[RetrievalTraceItem] = Field(default_factory=list)
    total_items: int = 0
    fallback_used: bool = True
    fallback_reason: str = "chroma_backend_not_accessible_or_fallback"
    chroma_modified: bool = False
    neo4j_accessed: bool = False
    chroma_query_attempted: bool = False
    chroma_hits_count: int = 0
    neo4j_query_attempted: bool = False
    evidence_pack_real_source_rows: int = 0
    citation_plan_real_citations: int = 0
    source_trace_real_rows: int = 0
    real_legal_retrieval_status: str = "none"


class LegalRetrievalRuntimeService:
    def __init__(self) -> None:
        self._current_backend_config: Optional[Dict[str, Any]] = None
        self._load_backend_config()

    def _load_backend_config(self) -> None:
        config_paths = [
            Path("d:/Python/Pycharm/Agent_data/legal_data/3.文件分类/vector_backends_k14a_clean/current_backend.json"),
        ]
        for cp in config_paths:
            if cp.exists():
                try:
                    self._current_backend_config = json.loads(cp.read_text(encoding="utf-8"))
                    return
                except Exception:
                    continue

    def retrieve(self, queries: List[str], collections: List[str],
                 profile: Any = None, top_k: int = 10) -> RetrievalTrace:
        trace = RetrievalTrace(
            retrieval_attempted=True,
            queries=queries,
            collections_queried=collections,
            backend_type=self._current_backend_config.get("backend_type", "unknown") if self._current_backend_config else "unknown",
            embedding_model=self._current_backend_config.get("embedding_model", "unknown") if self._current_backend_config else "unknown",
        )

        if not self._current_backend_config:
            trace.fallback_used = True
            trace.fallback_reason = "current_backend_config_not_found"
            trace.items = self._build_fallback_items(queries, collections)
            trace.total_items = len(trace.items)
            return trace

        try:
            trace.chroma_query_attempted = True
            items = self._query_chroma(queries, collections, top_k)
            if items:
                trace.retrieval_successful = True
                trace.real_legal_retrieval_used = True
                trace.fallback_used = False
                trace.retrieval_fallback_used = False
                trace.fallback_reason = ""
                trace.items = items
                trace.total_items = len(items)
                trace.chroma_hits_count = len(items)
                trace.real_legal_retrieval_status = "partial"
                return trace
        except Exception as exc:
            trace.fallback_reason = f"chroma_query_failed: {exc}"

        trace.items = self._build_fallback_items(queries, collections)
        trace.retrieval_fallback_used = True
        trace.total_items = len(trace.items)
        trace.real_legal_retrieval_status = "none"
        return trace

    def _query_chroma(self, queries: List[str], collections: List[str], top_k: int) -> List[RetrievalTraceItem]:
        import sys
        _project_root = Path(__file__).resolve().parents[4]
        if str(_project_root) not in sys.path:
            sys.path.insert(0, str(_project_root))

        from core.retrieval.current_backend_chroma_retriever import CurrentBackendChromaRetriever

        collection_map = {
            "data_transaction": ["rt5db2a1_cn_data_transaction"],
            "personal_information": ["rt5db2a1_cn_core_law_article", "rt5db2a1_cn_official_interpretation"],
            "cross_border_data_transfer": ["rt5db2a1_cn_crossborder"],
            "important_data": ["rt5db2a1_cn_core_law_article", "rt5db2a1_cn_crossborder"],
            "technical_standard": ["rt5db2a1_cn_technical_standard"],
        }
        allowed: List[str] = []
        for name in collections:
            allowed.extend(collection_map.get(name, [name if name.startswith("rt5db2a1_") else ""]))
        allowed = [name for name in dict.fromkeys(allowed) if name]

        retriever = CurrentBackendChromaRetriever()
        items: List[RetrievalTraceItem] = []
        seen: set[str] = set()
        embedding_model = self._current_backend_config.get("embedding_model", "D:/model/bge-m3") if self._current_backend_config else "D:/model/bge-m3"

        for query in queries:
            for candidate in retriever.search(query, top_k=top_k, allowed_collections=allowed):
                meta = candidate.get("metadata") or {}
                content = candidate.get("content") or {}
                chunk_id = str(meta.get("chunk_id") or meta.get("chromadb_id") or candidate.get("id") or "")
                source_id = str(meta.get("source_id") or meta.get("document_id") or content.get("source") or "")
                key = f"{source_id}:{chunk_id}"
                if key in seen:
                    continue
                seen.add(key)
                items.append(RetrievalTraceItem(
                    query=query[:200],
                    collection=str(meta.get("collection_name") or ""),
                    source_id=source_id,
                    chunk_id=chunk_id,
                    local_path=str(meta.get("local_path") or meta.get("source_path") or ""),
                    evidence_role=str(meta.get("evidence_role") or meta.get("citation_role_allowed") or "legal_basis"),
                    score=round(float(candidate.get("final_score") or candidate.get("score") or 0.0), 4),
                    retrieval_mode=f"canonical_current_backend_chroma_{embedding_model}",
                    fallback_used=False,
                ))
        return items

    def _build_fallback_items(self, queries: List[str], collections: List[str]) -> List[RetrievalTraceItem]:
        items: List[RetrievalTraceItem] = []
        fallback_rules = {
            "data_transaction": [
                ("数据安全法", "DSL"),
                ("个人信息保护法", "PIPL"),
                ("数据出境安全评估办法", "CROSS_BORDER"),
            ],
            "personal_information": [
                ("个人信息保护法", "PIPL"),
                ("App违法违规收集使用个人信息行为认定方法", "APP"),
            ],
            "cross_border_data_transfer": [
                ("数据出境安全评估办法", "CROSS_BORDER"),
                ("个人信息出境标准合同办法", "CROSS_BORDER_CONTRACT"),
                ("网络安全法", "CSL"),
            ],
            "important_data": [
                ("数据安全法", "DSL"),
                ("网络安全法", "CSL"),
            ],
        }

        for collection in collections:
            rules = fallback_rules.get(collection, [("通用法规", "GENERAL")])
            for law_name, law_id in rules:
                items.append(RetrievalTraceItem(
                    query=queries[0][:200] if queries else "",
                    collection=collection,
                    source_id=law_id,
                    chunk_id=f"{law_id}_fallback_{len(items)}",
                    local_path="",
                    evidence_role="legal_basis",
                    score=0.0,
                    retrieval_mode="rules_based_fallback",
                    fallback_used=True,
                ))

        return items
