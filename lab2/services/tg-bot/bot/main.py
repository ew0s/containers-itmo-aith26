from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import get_settings
from bot.gateway_client import GatewayClient
from bot.handlers import build_router


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    gateway_client = GatewayClient(
        base_url=str(settings.gateway_url),
        timeout=settings.gateway_timeout,
    )

    dp.include_router(build_router(gateway_client))

    try:
        await dp.start_polling(bot)
    finally:
        await gateway_client.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

