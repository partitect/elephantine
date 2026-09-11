from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from memagent.config import settings
from memagent.api.routes.health import router as health_router
from memagent.api.routes.memory import router as memory_router
from memagent.api.routes.dashboard import router as dashboard_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="MemAgent Core",
        description="Local-First, CPU-Native Cognitive AI Memory Engine",
        version="0.1.0",
        debug=settings.DEBUG
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, tags=["Health"])
    app.include_router(memory_router, tags=["Memory Primitives"])
    app.include_router(dashboard_router, tags=["Dashboard & Inspector"])

    return app

app = create_app()
