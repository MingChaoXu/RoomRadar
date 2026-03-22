from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from hotel_spider.api.router import api_router
from hotel_spider.core.config import get_settings
from hotel_spider.db.models import Base
from hotel_spider.db.session import engine
from hotel_spider.web.admin import router as admin_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.database_url.startswith("sqlite:///./"):
        Path("data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(admin_router)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/healthz", tags=["health"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
