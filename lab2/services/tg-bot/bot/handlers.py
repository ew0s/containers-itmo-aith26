from __future__ import annotations

import logging

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from bot.gateway_client import GatewayClient
from shared import schemas


def build_router(gateway_client: GatewayClient) -> Router:
    router = Router()
    logger = logging.getLogger(__name__)

    @router.message(CommandStart())
    async def cmd_start(message: types.Message, state: FSMContext) -> None:  # noqa: WPS430
        await state.clear()
        await message.answer(
            "Привет! Отправь мне пожелания по авто/мото/транспорту — "
            "подберу несколько вариантов на основе LLM."
        )

    @router.message(Command("history"))
    async def cmd_history(message: types.Message) -> None:  # noqa: WPS430
        user_id = str(message.from_user.id)
        try:
            history = await gateway_client.fetch_history(user_id)
        except Exception:
            logger.exception("Не удалось получить историю для %s", user_id)
            await message.answer("Не удалось получить историю 😔 Попробуй чуть позже.")
            return

        if not history.items:
            await message.answer("История пуста. Отправь запрос, и я его запомню!")
            return

        await message.answer(_format_history(history.items))

    @router.message(lambda msg: msg.text is not None and not msg.text.startswith("/"))
    async def handle_text(message: types.Message) -> None:  # noqa: WPS430
        if not message.text:
            await message.answer("Сообщение пустое, пришли текст с требованиями 🙏")
            return

        payload = schemas.GatewayMessageRequest(
            telegram_user_id=str(message.from_user.id),
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            text=message.text,
        )

        try:
            response = await gateway_client.send_message(payload)
        except Exception:
            logger.exception("Ошибка при отправке сообщения в gateway")
            await message.answer("Шлюз временно недоступен, попробуй чуть позже 🙌")
            return

        await message.answer(_format_reply(response.reply))

    return router


def _format_reply(reply: schemas.RecommendationResponse) -> str:
    lines = [reply.summary.strip(), ""]
    for idx, item in enumerate(reply.items, start=1):
        lines.append(f"{idx}. {item.name} — {item.category}")
        lines.append(f"   {item.description}")
        lines.append(f"   Примерный бюджет: {item.price_hint}")
        lines.append("")
    return "\n".join(lines).strip()


def _format_history(entries: list[schemas.HistoryEntry]) -> str:
    lines: list[str] = ["История последних сообщений:", ""]
    for entry in entries:
        lines.append(f"{entry.timestamp} — {entry.role}")
        lines.append(entry.content)
        lines.append("")
    return "\n".join(lines).strip()

