from __future__ import annotations

from typing import Any

import httpx
from fastapi import Request

from app.config import get_settings
from shared import schemas


class LlmClient:
    def __init__(self, base_url: str, timeout: float = 15.0):
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def recommend(self, payload: schemas.LlmRequest) -> schemas.RecommendationResponse:
        response = await self._client.post(
            "/api/v1/recommendations", json=payload.model_dump()
        )
        response.raise_for_status()
        data: Any = response.json()
        return schemas.RecommendationResponse(**data)

    async def aclose(self) -> None:
        await self._client.aclose()


def get_llm_client(request: Request) -> LlmClient:
    return request.app.state.llm_client

