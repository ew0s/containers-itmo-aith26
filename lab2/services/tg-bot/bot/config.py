from __future__ import annotations

from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(validation_alias="BOT_TOKEN")
    gateway_url: HttpUrl = Field(validation_alias="GATEWAY_URL")
    gateway_timeout: float = Field(10.0, validation_alias="BOT_GATEWAY_TIMEOUT")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

