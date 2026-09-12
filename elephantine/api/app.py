from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from elephantine.config import settings
from elephantine.api.routes.health import router as health_router
from elephantine.api.routes.memory import router as memory_router
from elephantine.api.routes.dashboard import router as dashboard_router

from contextlib import asynccontextmanager
from elephantine.api.routes.memory import get_container

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Replay pending transactional outbox events to LanceDB and start background engine
    container = get_container()
    await container.replay_pending_outbox()
    await container.sqlite_store.record_expired_events()
    await container.proactive_engine.start()
    yield
    # Shutdown: Stop proactive background evaluator daemon
    await container.proactive_engine.stop()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Elephantine Core",
        description="Local-First, CPU-Native Cognitive AI Memory Layer for Autonomous Agents",
        version="0.3.5",
        debug=settings.DEBUG,
        lifespan=lifespan
    )

    # Production-hardened CORS: if origins is wildcard, disable allow_credentials to adhere to browser spec
    allow_all = "*" in settings.CORS_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=not allow_all,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, tags=["Health"])
    app.include_router(memory_router, tags=["Memory Primitives"])
    app.include_router(dashboard_router, tags=["Dashboard & Inspector"])

    return app

app = create_app()
