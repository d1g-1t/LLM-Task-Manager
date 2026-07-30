from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://todo:todo@postgres:5432/todo"
    redis_url: str = "redis://redis:6379/0"

    llm_provider: Literal["openai", "mock"] = "mock"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_cache_ttl_seconds: int = Field(default=3600, ge=0)
    llm_request_timeout: int = Field(default=30, ge=1)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
