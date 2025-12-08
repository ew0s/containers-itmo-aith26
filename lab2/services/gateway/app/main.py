from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.config import get_settings
from app.llm_client import LlmClient
from app.routers import health, messages, users

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    llm_client = LlmClient(
        base_url=str(settings.llm_service_url),
        timeout=settings.llm_timeout_seconds,
    )
    app.state.llm_client = llm_client
    try:
        yield
    finally:
        await llm_client.aclose()


app = FastAPI(title="Gateway Service", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(messages.router)
app.include_router(users.router)

