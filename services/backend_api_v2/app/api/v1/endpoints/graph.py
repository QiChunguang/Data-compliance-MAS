from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.graph_read_service import Neo4jGraphReadService

router = APIRouter()
service = Neo4jGraphReadService()


@router.get("/health")
def graph_health() -> dict:
    return service.health()


@router.get("/overview")
def graph_overview() -> dict:
    return service.overview()


@router.get("/schema")
def graph_schema() -> dict:
    return service.schema()


@router.get("/subgraph")
def graph_subgraph(
    mode: str = Query(default="overview"),
    limit: int = Query(default=100, ge=1, le=300),
    node_id: str = "",
    q: str = "",
) -> dict:
    return service.subgraph(mode=mode, limit=limit, node_id=node_id, q=q)


@router.get("/search")
def graph_search(q: str = "", limit: int = Query(default=50, ge=1, le=100)) -> dict:
    return service.search(q=q, limit=limit)


@router.get("/node/{node_id}")
def graph_node(node_id: str) -> dict:
    return service.node(node_id)


@router.get("/neighbors/{node_id}")
def graph_neighbors(node_id: str, limit: int = Query(default=80, ge=1, le=200)) -> dict:
    return service.neighbors(node_id=node_id, limit=limit)
