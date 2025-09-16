"""Gerenciamento simples de autenticação GLPI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from glpi_dashboard_shared.config.settings import settings


@dataclass(slots=True)
class GLPISession:
    """Representa tokens de sessão GLPI usados pelos clientes HTTP."""

    app_token: str
    user_token: str

    @classmethod
    def from_settings(cls) -> 'GLPISession':
        return cls(app_token=settings.glpi_app_token, user_token=settings.glpi_user_token)

    def as_headers(self) -> Mapping[str, str]:
        return {
            'App-Token': self.app_token,
            'Authorization': f'user_token {self.user_token}',
        }
