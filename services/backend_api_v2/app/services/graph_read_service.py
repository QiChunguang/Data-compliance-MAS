from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_GRAPH_VERSION = "phase10k14a5db2a1_clean_primary_authority"


def _dotenv_value(name: str) -> str:
    env_path = Path(__file__).resolve().parents[4] / ".env"
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'")
    except OSError:
        return ""
    return ""


def _mask(text: str) -> str:
    if not text:
        return ""
    if len(text) <= 2:
        return "**"
    return f"{text[:1]}***{text[-1:]}"


class Neo4jGraphReadService:
    """Read-only Neo4j browser API. Never returns or logs credentials."""

    def __init__(self) -> None:
        self.uri = os.getenv("NEO4J_URI") or os.getenv("REGUTHINK_NEO4J_URI") or _dotenv_value("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER") or os.getenv("REGUTHINK_NEO4J_USER") or _dotenv_value("NEO4J_USER") or "neo4j"
        self.password = os.getenv("NEO4J_PASSWORD") or os.getenv("REGUTHINK_NEO4J_PASSWORD") or _dotenv_value("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE") or os.getenv("REGUTHINK_NEO4J_DATABASE") or _dotenv_value("NEO4J_DATABASE") or "neo4j"
        self.graph_version = os.getenv("REGUTHINK_NEO4J_GRAPH_VERSION") or _dotenv_value("REGUTHINK_NEO4J_GRAPH_VERSION") or EXPECTED_GRAPH_VERSION
        self.timeout_seconds = float(os.getenv("REGUTHINK_NEO4J_READ_TIMEOUT_SECONDS") or "2.5")

    def health(self) -> Dict[str, Any]:
        try:
            with self._driver() as driver:
                driver.verify_connectivity()
            return {
                "status": "ok",
                "graph_available": True,
                "uri_configured": bool(self.uri),
                "user_configured": bool(self.user),
                "password_configured": bool(self.password),
                "database_masked": _mask(self.database),
                "graph_version": self.graph_version,
                "readonly": True,
            }
        except Exception as exc:
            return self._unavailable(exc)

    def overview(self) -> Dict[str, Any]:
        unavailable = self._connectivity_error()
        if unavailable:
            return unavailable
        try:
            with self._driver() as driver, driver.session(database=self.database) as session:
                label_rows = session.run(
                    """
                    MATCH (n)
                    WHERE $graph_version = '' OR n.graph_version = $graph_version
                    UNWIND labels(n) AS label
                    RETURN label, count(*) AS count
                    ORDER BY count DESC
                    """,
                    graph_version=self.graph_version,
                )
                rel_rows = session.run(
                    """
                    MATCH (a)-[r]->(b)
                    WHERE $graph_version = '' OR (a.graph_version = $graph_version AND b.graph_version = $graph_version)
                    RETURN type(r) AS type, count(*) AS count
                    ORDER BY count DESC
                    """,
                    graph_version=self.graph_version,
                )
                node_counts = {str(r["label"]): int(r["count"]) for r in label_rows}
                edge_counts = {str(r["type"]): int(r["count"]) for r in rel_rows}
            state = "ok" if node_counts else "graph_empty"
            return {
                "status": state,
                "graph_available": True,
                "graph_empty": not bool(node_counts),
                "node_counts_by_label": node_counts,
                "edge_counts_by_type": edge_counts,
                "graph_version": self.graph_version,
                "database_masked": _mask(self.database),
                "readonly": True,
            }
        except Exception as exc:
            return self._unavailable(exc)

    def schema(self) -> Dict[str, Any]:
        overview = self.overview()
        if overview.get("status") in {"graph_unavailable", "graph_empty"}:
            return overview
        return {
            "status": "ok",
            "labels": sorted((overview.get("node_counts_by_label") or {}).keys()),
            "relationship_types": sorted((overview.get("edge_counts_by_type") or {}).keys()),
            "graph_version": self.graph_version,
            "readonly": True,
        }

    def subgraph(self, limit: int = 100, mode: str = "overview", node_id: str = "", q: str = "") -> Dict[str, Any]:
        unavailable = self._connectivity_error()
        if unavailable:
            return {**unavailable, "nodes": [], "edges": []}
        safe_limit = max(1, min(int(limit or 100), 300))
        mode = (mode or "overview").strip().lower()
        if mode == "source" and node_id:
            return self.neighbors(node_id=node_id, limit=safe_limit, mode=mode)
        if mode == "topic" and (node_id or q):
            return self._topic_focus(node_id=node_id, q=q, limit=safe_limit)
        if mode == "search" and q:
            return self.search(q=q, limit=min(safe_limit, 100), include_neighbors=True)
        try:
            with self._driver() as driver, driver.session(database=self.database) as session:
                edge_rows = session.run(
                    """
                    MATCH (a)-[r]->(b)
                    WHERE ($graph_version = '' OR (a.graph_version = $graph_version AND b.graph_version = $graph_version))
                      AND any(label IN labels(a) WHERE label IN $default_labels)
                      AND any(label IN labels(b) WHERE label IN $default_labels)
                      AND NOT 'Chunk' IN labels(a)
                      AND NOT 'Chunk' IN labels(b)
                    RETURN elementId(a) AS source, labels(a) AS source_labels, properties(a) AS source_props,
                           elementId(b) AS target, labels(b) AS target_labels, properties(b) AS target_props,
                           elementId(r) AS id, type(r) AS type, properties(r) AS props
                    LIMIT $edge_limit
                    """,
                    graph_version=self.graph_version,
                    default_labels=[
                        "Source",
                        "Document",
                        "Article",
                        "Clause",
                        "Topic",
                        "CaseProfile",
                        "CitationRule",
                        "ClaimTemplate",
                        "ChromaCollection",
                    ],
                    edge_limit=safe_limit * 2,
                )
                node_map: Dict[str, Dict[str, Any]] = {}
                edges: List[Dict[str, Any]] = []
                for row in edge_rows:
                    node_map.setdefault(
                        str(row["source"]),
                        self._node_from_parts(row["source"], row["source_labels"], row["source_props"]),
                    )
                    node_map.setdefault(
                        str(row["target"]),
                        self._node_from_parts(row["target"], row["target_labels"], row["target_props"]),
                    )
                    edges.append(self._edge(row))
                nodes = list(node_map.values())[:safe_limit]
                node_ids = {n["id"] for n in nodes}
                edges = [edge for edge in edges if edge["source"] in node_ids and edge["target"] in node_ids][: safe_limit * 2]
            status = "ok" if nodes else "graph_empty"
            return {
                "status": status,
                "graph_empty": not bool(nodes),
                "nodes": nodes,
                "edges": edges,
                "mode": mode,
                "limit": safe_limit,
                "graph_version": self.graph_version,
                "readonly": True,
            }
        except Exception as exc:
            return {**self._unavailable(exc), "nodes": [], "edges": []}

    def search(self, q: str, limit: int = 50, include_neighbors: bool = False) -> Dict[str, Any]:
        text = (q or "").strip()
        if not text:
            return {"status": "ok", "query": text, "nodes": [], "edges": [], "readonly": True}
        unavailable = self._connectivity_error()
        if unavailable:
            return {**unavailable, "query": text, "nodes": [], "edges": []}
        try:
            with self._driver() as driver, driver.session(database=self.database) as session:
                rows = session.run(
                    """
                    MATCH (n)
                    WHERE ($graph_version = '' OR n.graph_version = $graph_version)
                      AND any(v IN [x IN keys(n) | toString(n[x])] WHERE toLower(v) CONTAINS toLower($q))
                    RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props
                    LIMIT $limit
                    """,
                    graph_version=self.graph_version,
                    q=text,
                    limit=max(1, min(limit, 100)),
                )
                nodes = [self._node(row) for row in rows]
                if include_neighbors and nodes:
                    return self._nodes_with_edges(session, [n["id"] for n in nodes], limit=max(limit, 80), query=text, mode="search")
            return {"status": "ok" if nodes else "graph_empty", "query": text, "nodes": nodes, "edges": [], "readonly": True}
        except Exception as exc:
            return {**self._unavailable(exc), "query": text, "nodes": [], "edges": []}

    def node(self, node_id: str) -> Dict[str, Any]:
        unavailable = self._connectivity_error()
        if unavailable:
            return unavailable
        try:
            with self._driver() as driver, driver.session(database=self.database) as session:
                row = session.run(
                    """
                    MATCH (n)
                    WHERE elementId(n) = $node_id
                    RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props
                    LIMIT 1
                    """,
                    node_id=node_id,
                ).single()
            if not row:
                return {"status": "not_found", "node_id": node_id, "readonly": True}
            return {"status": "ok", "node": self._node(row, full=True), "readonly": True}
        except Exception as exc:
            return self._unavailable(exc)

    def neighbors(self, node_id: str, limit: int = 80, mode: str = "neighbors") -> Dict[str, Any]:
        unavailable = self._connectivity_error()
        if unavailable:
            return {**unavailable, "nodes": [], "edges": []}
        safe_limit = max(1, min(int(limit or 80), 200))
        try:
            with self._driver() as driver, driver.session(database=self.database) as session:
                return self._nodes_with_edges(session, [node_id], limit=safe_limit, mode=mode, focus_node_id=node_id)
        except Exception as exc:
            return {**self._unavailable(exc), "nodes": [], "edges": []}

    def _topic_focus(self, node_id: str, q: str, limit: int) -> Dict[str, Any]:
        try:
            with self._driver() as driver, driver.session(database=self.database) as session:
                if node_id:
                    return self._nodes_with_edges(session, [node_id], limit=limit, mode="topic", focus_node_id=node_id)
                row = session.run(
                    """
                    MATCH (n:Topic)
                    WHERE ($graph_version = '' OR n.graph_version = $graph_version)
                      AND any(v IN [x IN keys(n) | toString(n[x])] WHERE toLower(v) CONTAINS toLower($q))
                    RETURN elementId(n) AS id
                    LIMIT 1
                    """,
                    graph_version=self.graph_version,
                    q=(q or "").strip(),
                ).single()
                if not row:
                    row = session.run(
                        """
                        MATCH (n:Topic)
                        WHERE $graph_version = '' OR n.graph_version = $graph_version
                        RETURN elementId(n) AS id
                        LIMIT 1
                        """,
                        graph_version=self.graph_version,
                    ).single()
                if not row:
                    return {"status": "graph_empty", "query": q, "nodes": [], "edges": [], "mode": "topic", "readonly": True}
                return self._nodes_with_edges(session, [str(row["id"])], limit=limit, mode="topic", focus_node_id=str(row["id"]))
        except Exception as exc:
            return {**self._unavailable(exc), "nodes": [], "edges": []}

    def _nodes_with_edges(
        self,
        session: Any,
        seed_ids: List[str],
        *,
        limit: int,
        mode: str,
        query: str = "",
        focus_node_id: str = "",
    ) -> Dict[str, Any]:
        rows = session.run(
            """
            MATCH (n)
            WHERE elementId(n) IN $seed_ids
            OPTIONAL MATCH p=(n)-[r]-(m)
            WHERE $graph_version = '' OR m.graph_version = $graph_version
            WITH collect(DISTINCT n) + collect(DISTINCT m) AS raw_nodes,
                 collect(DISTINCT r) AS raw_rels
            UNWIND raw_nodes AS node
            WITH collect(DISTINCT node)[0..$limit] AS nodes, raw_rels
            UNWIND nodes AS out_node
            RETURN elementId(out_node) AS id, labels(out_node) AS labels, properties(out_node) AS props
            """,
            seed_ids=seed_ids,
            graph_version=self.graph_version,
            limit=limit,
        )
        nodes = [self._node(row) for row in rows]
        node_ids = [n["id"] for n in nodes]
        edge_rows = session.run(
            """
            MATCH (a)-[r]-(b)
            WHERE elementId(a) IN $node_ids AND elementId(b) IN $node_ids
            RETURN elementId(r) AS id, elementId(a) AS source, elementId(b) AS target,
                   type(r) AS type, properties(r) AS props
            LIMIT $limit
            """,
            node_ids=node_ids,
            limit=limit * 2,
        )
        edges = [self._edge(row) for row in edge_rows]
        return {
            "status": "ok" if nodes else "graph_empty",
            "graph_empty": not bool(nodes),
            "nodes": nodes,
            "edges": edges,
            "mode": mode,
            "query": query,
            "focus_node_id": focus_node_id,
            "limit": limit,
            "graph_version": self.graph_version,
            "readonly": True,
        }

    def _driver(self) -> Any:
        if not self.uri:
            raise RuntimeError("Graph database URI is not configured for the public showcase.")
        from neo4j import GraphDatabase
        return GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            connection_timeout=self.timeout_seconds,
            max_transaction_retry_time=self.timeout_seconds,
        )

    def _connectivity_error(self) -> Dict[str, Any] | None:
        health = self.health()
        return health if health.get("status") == "graph_unavailable" else None

    def _unavailable(self, exc: Exception) -> Dict[str, Any]:
        return {
            "status": "graph_unavailable",
            "graph_available": False,
            "reason": type(exc).__name__,
            "message": "Neo4j read-only graph is unavailable. Credentials are configured only on the backend and are not exposed.",
            "database_masked": _mask(self.database),
            "graph_version": self.graph_version,
            "readonly": True,
        }

    def _node(self, row: Any, full: bool = False) -> Dict[str, Any]:
        props = dict(row["props"] or {})
        labels = list(row["labels"] or [])
        return self._node_from_parts(row["id"], labels, props, full=full)

    def _node_from_parts(self, node_id: Any, labels: Any, props: Any, full: bool = False) -> Dict[str, Any]:
        props = dict(props or {})
        labels = list(labels or [])
        label = str(props.get("title") or props.get("name") or props.get("source_title") or props.get("case_id") or node_id)
        summary_keys = ["source_id", "document_id", "article_id", "case_id", "graph_version", "collection_name", "source_type"]
        summary = {k: props.get(k) for k in summary_keys if props.get(k) is not None}
        if full:
            summary.update({k: v for k, v in props.items() if k not in {"password", "secret", "api_key"}})
        return {
            "id": str(node_id),
            "label": label[:120],
            "type": labels[0] if labels else "Node",
            "labels": labels,
            "properties_summary": summary,
            "source_id": str(props.get("source_id") or ""),
        }

    def _edge(self, row: Any) -> Dict[str, Any]:
        props = dict(row["props"] or {})
        return {
            "id": str(row["id"]),
            "source": str(row["source"]),
            "target": str(row["target"]),
            "type": str(row["type"]),
            "properties_summary": {k: v for k, v in props.items() if k not in {"password", "secret", "api_key"}},
        }
