from __future__ import annotations

import logging
import re
from typing import Any

from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_mistralai.chat_models import ChatMistralAI

from app.config import Settings
from shared import schemas

logger = logging.getLogger(__name__)


class RecommendationEngine:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._chain: Runnable | None = None
        self._parser: StructuredOutputParser | None = None
        if settings.mistral_api_key:
            response_schemas = [
                ResponseSchema(
                    name="summary",
                    description="Краткое текстовое объяснение рекомендаций на русском языке.",
                ),
                ResponseSchema(
                    name="items",
                    description=(
                        "Список объектов с подробным описанием транспорта. "
                        "Каждый элемент должен содержать поля name, category, description, price_hint."
                    ),
                ),
            ]
            parser = StructuredOutputParser.from_response_schemas(response_schemas)
            format_instructions = parser.get_format_instructions()
            escaped_instructions = (
                format_instructions.replace("{", "{{").replace("}", "}}")
            )
            model = ChatMistralAI(
                api_key=settings.mistral_api_key,
                model=settings.mistral_model,
                temperature=0.2,
                max_output_tokens=1024,
            )
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Ты — эксперт по подбору транспортных средств. "
                        "Подбирай максимум "
                        f"{settings.max_items} вариантов, учитывая бюджет, тип и другие пожелания. "
                        "Следуй формату ниже и не добавляй поясняющий текст.\n"
                        f"{escaped_instructions}",
                    ),
                    (
                        "human",
                        "Запрос пользователя: {query}\n"
                        "История диалога (может быть пустой):\n{history}\n",
                    ),
                ]
            )
            self._chain = prompt | model | StrOutputParser()
            self._parser = parser
        else:
            logger.warning("Mistral API key is not configured; LLM responses will be placeholders")

    async def recommend(self, payload: schemas.LlmRequest) -> schemas.RecommendationResponse:
        history_block = "\n".join(f"{item.role}: {item.content}" for item in payload.history)
        logger.info(
            "LLM request received",
            extra={
                "query": payload.query[:200],
                "history_len": len(payload.history),
            },
        )

        if self._chain is None:
            return self._unavailable_response(
                "LLM-сервис не настроен. Проверь ключ Mistral и попробуй снова."
            )

        try:
            raw = await self._chain.ainvoke({"query": payload.query, "history": history_block})
            parsed = self._parse_response(raw)
            if parsed:
                logger.info(
                    "LLM response parsed",
                    extra={"items": len(parsed.items), "summary_len": len(parsed.summary)},
                )
                return parsed
            logger.error("LLM вернул неожиданный формат: %s", raw)
        except Exception as exc:
            logger.exception("LLM call failed: %s", exc)

        return self._unavailable_response("LLM временно недоступен. Попробуй ещё раз позже.")

    def _parse_response(self, raw: Any) -> schemas.RecommendationResponse | None:
        if not raw or self._parser is None:
            return None
        cleaned = self._clean_response(raw)
        if not cleaned:
            return None
        try:
            data = self._parser.parse(cleaned)
            return schemas.RecommendationResponse(**data)
        except Exception as exc:
            logger.error("Failed to parse LLM response: %s", exc)
            return None

    def _clean_response(self, raw: Any) -> str | None:
        if not isinstance(raw, str):
            return None
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[\w-]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        return cleaned.strip()

    def _unavailable_response(self, message: str) -> schemas.RecommendationResponse:
        return schemas.RecommendationResponse(summary=message, items=[])

