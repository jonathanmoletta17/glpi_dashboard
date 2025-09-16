"""Configuração tipada compartilhada entre API, workers e agregadores.

O módulo segue o princípio de centralizar configurações sensíveis em uma única
fonte, conforme `01_Principios_Arquitetura.md` e o contrato de governança do Doc
05. Usamos `pydantic-settings` para validar tipos e permitir _overrides_ por
variáveis de ambiente ou arquivos `.env`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração principal do ecossistema GLPI Dashboard.

    Cada atributo representa um parâmetro de infraestrutura citado na
    documentação: URLs do GLPI, parâmetros de autenticação, credenciais e
    opções de observabilidade. Todos recebem valores "seguros" para execução
    local com fixtures, mas podem ser sobrescritos em produção.
    """

    model_config = SettingsConfigDict(env_file=('.env', '.env.local'), env_prefix='GLPI_DASHBOARD_')

    environment: Literal['local', 'staging', 'production'] = Field(
        default='local',
        description='Define o modo de execução para habilitar/desabilitar mocks.'
    )
    glpi_base_url: str = Field(
        default='https://glpi.example/api',
        description='URL base da API GLPI; usada pelos workers de ingestão.'
    )
    glpi_app_token: str = Field(
        default='changeme-app-token',
        description='Token de aplicação GLPI. Em execução local usamos valor de placeholder.'
    )
    glpi_user_token: str = Field(
        default='changeme-user-token',
        description='Token de usuário GLPI com permissão de leitura.'
    )
    data_directory: Path = Field(
        default=Path('data'),
        description='Diretório onde o worker persiste snapshots e métricas agregadas.'
    )
    cache_url: str = Field(
        default='redis://localhost:6379/0',
        description='Endpoint do Redis utilizado para caching e rate limiting.'
    )
    enable_metrics: bool = Field(
        default=True,
        description='Habilita a coleta de métricas Prometheus nos aplicativos.'
    )
    log_level: str = Field(
        default='INFO',
        description='Nível de log padrão para todos os serviços.'
    )
    tracing_endpoint: Optional[str] = Field(
        default=None,
        description='Endpoint OpenTelemetry para exportar traces. Mantém None em execução local.'
    )

    def resolved_data_directory(self) -> Path:
        """Garante que o diretório de dados exista e retorna o caminho absoluto."""

        directory = self.data_directory.expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        return directory


settings = Settings()
"""Instância carregada no import garantindo cache de configuração."""
