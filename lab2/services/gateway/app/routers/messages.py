from __future__ import annotations

from typing import Sequence
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.sql import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.llm_client import LlmClient, get_llm_client
import shared.models as models
from shared import schemas

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])
settings = get_settings()
logger = logging.getLogger(__name__)


@router.post("", response_model=schemas.GatewayMessageResponse)
async def process_message(
    payload: schemas.GatewayMessageRequest,
    session: AsyncSession = Depends(get_session),
    llm_client: LlmClient = Depends(get_llm_client),
) -> schemas.GatewayMessageResponse:
    user = await _get_or_create_user(session, payload)
    logger.info(
        "Получено сообщение",
        extra={
            "telegram_user_id": payload.telegram_user_id,
            "message_len": len(payload.text),
        },
    )

    user_message = models.Message(
        user_id=user.id, role=models.MessageRole.USER, content=payload.text
    )
    session.add(user_message)
    await session.flush()

    history = await _load_history(session, user.id, settings.history_limit)

    try:
        llm_response = await llm_client.recommend(
            schemas.LlmRequest(query=payload.text, history=history)
        )
    except httpx.HTTPError as http_error:
        await session.commit()
        logger.error("LLM сервис недоступен: %s", http_error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM сервис недоступен: {http_error}",
        ) from http_error

    assistant_message = models.Message(
        user_id=user.id,
        role=models.MessageRole.ASSISTANT,
        content=llm_response.summary,
    )
    session.add(assistant_message)
    await session.commit()
    logger.info(
        "Ответ отправлен пользователю",
        extra={
            "telegram_user_id": payload.telegram_user_id,
            "items": len(llm_response.items),
        },
    )

    return schemas.GatewayMessageResponse(reply=llm_response)


async def _get_or_create_user(
    session: AsyncSession, payload: schemas.GatewayMessageRequest
) -> models.User:
    stmt: Select[tuple[models.User]] = select(models.User).where(
        models.User.telegram_user_id == payload.telegram_user_id
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        updated = False
        for field in ("username", "first_name", "last_name"):
            new_value = getattr(payload, field)
            if new_value and getattr(user, field) != new_value:
                setattr(user, field, new_value)
                updated = True
        if updated:
            await session.flush()
        return user

    user = models.User(
        telegram_user_id=payload.telegram_user_id,
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    session.add(user)
    await session.flush()
    return user


async def _load_history(
    session: AsyncSession, user_id: int, limit: int
) -> list[schemas.MessageHistoryItem]:
    stmt: Select[tuple[models.Message]] = (
        select(models.Message)
        .where(models.Message.user_id == user_id)
        .order_by(models.Message.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    messages: Sequence[models.Message] = result.scalars().all()
    ordered = list(reversed(messages))
    return [
        schemas.MessageHistoryItem(role=message.role.value, content=message.content)
        for message in ordered
    ]

