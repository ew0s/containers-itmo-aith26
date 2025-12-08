from __future__ import annotations

from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(validation_alias="DATABASE_URL")
    llm_service_url: HttpUrl = Field(validation_alias="LLM_SERVICE_URL")
    llm_timeout_seconds: float = Field(15.0, validation_alias="LLM_TIMEOUT_SECONDS")
    history_limit: int = Field(6, validation_alias="HISTORY_LIMIT")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

