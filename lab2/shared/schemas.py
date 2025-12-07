from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class MessageHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class RecommendationItem(BaseModel):
    name: str
    category: str
    description: str
    price_hint: str = Field(description="Краткое описание бюджета/стоимости")


class RecommendationResponse(BaseModel):
    summary: str
    items: List[RecommendationItem]


class HistoryEntry(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: str


class HistoryResponse(BaseModel):
    items: List[HistoryEntry] = Field(default_factory=list)


class LlmRequest(BaseModel):
    query: str
    history: List[MessageHistoryItem] = Field(default_factory=list)


class GatewayMessageRequest(BaseModel):
    telegram_user_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    text: str


class GatewayMessageResponse(BaseModel):
    reply: RecommendationResponse


class BotReply(BaseModel):
    reply_text: str

