from __future__ import annotations

from typing import Any

import httpx

from shared import schemas


class GatewayClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def send_message(
        self, payload: schemas.GatewayMessageRequest
    ) -> schemas.GatewayMessageResponse:
        response = await self._client.post("/api/v1/messages", json=payload.model_dump())
        response.raise_for_status()
        data: Any = response.json()
        return schemas.GatewayMessageResponse(**data)

    async def fetch_history(
        self, telegram_user_id: str, limit: int = 10
    ) -> schemas.HistoryResponse:
        response = await self._client.get(
            f"/api/v1/users/{telegram_user_id}/history", params={"limit": limit}
        )
        response.raise_for_status()
        data: Any = response.json()
        return schemas.HistoryResponse(**data)

    async def aclose(self) -> None:
        await self._client.aclose()

