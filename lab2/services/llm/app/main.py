from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.config import get_settings
from app.engine import RecommendationEngine
from shared import schemas


settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = RecommendationEngine(settings)
    app.state.engine = engine
    yield


app = FastAPI(title="LLM Recommendation Service", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/recommendations", response_model=schemas.RecommendationResponse)
async def create_recommendation(payload: schemas.LlmRequest) -> schemas.RecommendationResponse:
    engine: RecommendationEngine = app.state.engine
    return await engine.recommend(payload)

