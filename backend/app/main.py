from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import analysis, auth, bills, extract, health, properties, report
from app.config import get_settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # MVP: create tables on startup. Replace with Alembic migrations before production.
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        summary="Analyze water & electricity bills to detect anomalies, leaks, and savings.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(properties.router)
    app.include_router(bills.router)
    app.include_router(extract.router)
    app.include_router(analysis.router)
    app.include_router(report.router)
    return app


app = create_app()
