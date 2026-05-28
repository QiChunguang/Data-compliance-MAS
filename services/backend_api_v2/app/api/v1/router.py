from fastapi import APIRouter

from app.api.v1.endpoints import artifacts, assessments, baseline, cases, chat, conversations, files, graph, health, jobs, runtime, stream

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(baseline.router, prefix="/baseline", tags=["baseline"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(artifacts.router, prefix="/cases", tags=["artifacts"])
api_router.include_router(runtime.router, prefix="/runtime", tags=["runtime"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(chat.router, prefix="/conversations", tags=["chat"])
api_router.include_router(files.router, tags=["files"])
api_router.include_router(assessments.router, tags=["assessments"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(stream.router, tags=["stream"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
