from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mistral_api_key: str | None = Field(default=None, validation_alias="MISTRAL_API_KEY")
    mistral_model: str = Field("mistral-large-latest", validation_alias="MISTRAL_MODEL")
    max_items: int = Field(3, validation_alias="LLM_MAX_ITEMS")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

