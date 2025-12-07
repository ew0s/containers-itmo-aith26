from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from shared import schemas
import shared.models as models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/{telegram_user_id}/history", response_model=schemas.HistoryResponse)
async def get_user_history(
    telegram_user_id: str,
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> schemas.HistoryResponse:
    user_stmt = select(models.User).where(models.User.telegram_user_id == telegram_user_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if not user:
        logger.info("История не найдена для пользователя %s", telegram_user_id)
        return schemas.HistoryResponse(items=[])

    message_stmt = (
        select(models.Message)
        .where(models.Message.user_id == user.id)
        .order_by(models.Message.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(message_stmt)
    messages = list(reversed(result.scalars().all()))

    items = [
        schemas.HistoryEntry(
            role=message.role.value,
            content=message.content,
            timestamp=_format_dt(message.created_at),
        )
        for message in messages
    ]
    logger.info(
        "История отправлена пользователю %s; записей=%s",
        telegram_user_id,
        len(items),
    )
    return schemas.HistoryResponse(items=items)


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone().isoformat()


