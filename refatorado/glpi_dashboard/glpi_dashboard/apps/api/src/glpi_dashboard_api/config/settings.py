"""Configurações específicas da API pública."""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=('.env', '.env.local'), env_prefix='GLPI_API_')

    host: str = Field(default='0.0.0.0')
    port: int = Field(default=8000)
    cors_origins: list[str] = Field(default_factory=lambda: ['*'])
    enable_docs: bool = Field(default=True)


def load_api_settings() -> ApiSettings:
    return ApiSettings()
