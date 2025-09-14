# -*- coding: utf-8 -*-
"""
GLPI Metrics Adapter - Adaptador para acesso à API do GLPI.

Este módulo implementa o padrão Adapter para abstrair o acesso à API do GLPI,
fornecendo uma interface limpa e testável para consultas de métricas.
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import httpx
import asyncio

# Importar DTOs centrais para evitar duplicação
from ....application.dto.metrics_dto import MetricsFilterDTO, TechnicianLevel
from ....application.queries.metrics_query import QueryContext, MetricsDataSource

logger = logging.getLogger(__name__)


class GLPIConnectionError(Exception):
    """Exceção para erros de conexão com GLPI."""

    pass


class GLPIAuthenticationError(Exception):
    """Exceção para erros de autenticação com GLPI."""

    pass


class GLPIAPIError(Exception):
    """Exceção para erros da API GLPI."""

    pass


@dataclass
class GLPIConfig:
    """Configuração para conexão com GLPI."""

    base_url: str
    app_token: str
    user_token: str
    timeout: int = 30  # Changed parameter name to match usage
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    session_timeout_minutes: int = 60

    def __post_init__(self):
        # Remover trailing slash da URL
        self.base_url = self.base_url.rstrip("/")


class GLPISessionManager:
    """Gerenciador de sessão GLPI com renovação automática."""

    def __init__(self, config: GLPIConfig):
        self.config = config
        self.session_token: Optional[str] = None
        self.session_expires_at: Optional[datetime] = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def get_session_token(self, correlation_id: Optional[str] = None) -> str:
        """Obtém token de sessão válido, renovando se necessário."""
        if self._is_session_valid():
            if self.session_token is None:
                raise GLPIAuthenticationError("Token de sessão inválido")
            return self.session_token

        await self._create_new_session(correlation_id)
        if self.session_token is None:
            raise GLPIAuthenticationError("Falha ao obter token de sessão")
        return self.session_token

    def _is_session_valid(self) -> bool:
        """Verifica se a sessão atual é válida."""
        if not self.session_token or not self.session_expires_at:
            return False

        # Renovar 5 minutos antes do vencimento
        buffer_time = timedelta(minutes=5)
        return datetime.now() < (self.session_expires_at - buffer_time)

    async def _create_new_session(self, correlation_id: Optional[str] = None) -> None:
        """Cria nova sessão GLPI."""
        headers = {
            "Content-Type": "application/json",
            "App-Token": self.config.app_token,
            "Authorization": f"user_token {self.config.user_token}",
        }

        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        url = f"{self.config.base_url}/apirest.php/initSession"

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    self.session_token = data.get("session_token")

                    # Definir expiração da sessão
                    self.session_expires_at = datetime.now() + timedelta(minutes=self.config.session_timeout_minutes)

                    self.logger.info(
                        "Nova sessão GLPI criada",
                        extra={
                            "correlation_id": correlation_id,
                            "expires_at": self.session_expires_at.isoformat(),
                        },
                    )
                else:
                    raise GLPIAuthenticationError(f"Falha na autenticação GLPI: {response.status_code} - {response.text}")

        except httpx.RequestError as e:
            raise GLPIConnectionError(f"Erro de conexão com GLPI: {str(e)}")
        except Exception as e:
            raise GLPIAPIError(f"Erro inesperado na autenticação GLPI: {str(e)}")

    async def close_session(self, correlation_id: Optional[str] = None) -> None:
        """Fecha sessão GLPI."""
        if not self.session_token:
            return

        headers = {
            "Session-Token": self.session_token,
            "App-Token": self.config.app_token,
        }

        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        url = f"{self.config.base_url}/apirest.php/killSession"

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    self.logger.info(
                        "Sessão GLPI fechada",
                        extra={"correlation_id": correlation_id},
                    )
        except Exception as e:
            self.logger.warning(
                f"Erro ao fechar sessão GLPI: {str(e)}",
                extra={"correlation_id": correlation_id},
            )
        finally:
            self.session_token = None
            self.session_expires_at = None


class GLPIAPIClient:
    """Cliente HTTP para API GLPI."""

    def __init__(self, config: GLPIConfig, session_manager: GLPISessionManager):
        self.config = config
        self.session_manager = session_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Faz requisição autenticada para API GLPI."""

        session_token = await self.session_manager.get_session_token(correlation_id)

        headers = {
            "Content-Type": "application/json",
            "Session-Token": session_token,
            "App-Token": self.config.app_token,
        }

        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        # Construir URL
        url = f"{self.config.base_url}/apirest.php/{endpoint.lstrip('/')}"
        if params:
            url += f"?{urlencode(params, doseqs=True)}"

        # Log da requisição
        self.logger.debug(
            f"GLPI API Request: {method} {url}",
            extra={
                "correlation_id": correlation_id,
                "method": method,
                "endpoint": endpoint,
                "params": params,
            },
        )

        try:
            request_kwargs = {"headers": headers}

            if data:
                request_kwargs["json"] = data

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.request(method, url, **request_kwargs)
                response_text = response.text

                # Log da resposta
                self.logger.debug(
                    f"GLPI API Response: {response.status_code}",
                    extra={
                        "correlation_id": correlation_id,
                        "status_code": response.status_code,
                        "response_size": len(response_text),
                    },
                )

                if response.status_code == 200:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        # Algumas respostas podem não ser JSON
                        return {"raw_response": response_text}

                elif response.status_code == 401:
                    # Token expirado, forçar renovação
                    self.session_manager.session_token = None
                    raise GLPIAuthenticationError(f"Token expirado: {response_text}")

                else:
                    raise GLPIAPIError(f"Erro na API GLPI: {response.status_code} - {response_text}")

        except httpx.RequestError as e:
            raise GLPIConnectionError(f"Erro de conexão com GLPI: {str(e)}")
        except Exception as e:
            if isinstance(e, (GLPIConnectionError, GLPIAuthenticationError, GLPIAPIError)):
                raise
            raise GLPIAPIError(f"Erro inesperado na API GLPI: {str(e)}")


class GLPIMetricsAdapter:
    """Adaptador para métricas do GLPI."""

    def __init__(self, config: GLPIConfig):
        self.config = config
        self.session_manager = GLPISessionManager(config)
        self.api_client = GLPIAPIClient(config, self.session_manager)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Cache para hierarquia de técnicos (válido por 1 hora)
        self._technician_hierarchy_cache: Optional[Dict[int, str]] = None
        self._hierarchy_cache_expires_at: Optional[datetime] = None

    async def get_ticket_count_by_hierarchy(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> Dict[str, Any]:
        """Obtém contagem de tickets por hierarquia."""
        correlation_id = context.correlation_id if context else None

        try:
            # Obter hierarquia de técnicos
            technician_hierarchy = await self.get_technician_hierarchy(context)

            # Construir parâmetros da consulta
            params = self._build_ticket_query_params(filters)

            # Fazer requisição para tickets
            tickets_data = await self.api_client.make_request(endpoint="Ticket", params=params, correlation_id=correlation_id)

            # Processar dados por hierarquia
            hierarchy_metrics = self._process_tickets_by_hierarchy(tickets_data, technician_hierarchy, correlation_id)

            return {"levels": hierarchy_metrics}

        except Exception as e:
            self.logger.error(
                f"Erro ao obter tickets por hierarquia: {str(e)}",
                extra={"correlation_id": correlation_id},
            )
            raise

    async def get_technician_metrics(
        self,
        technician_id: Optional[int] = None,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> List[Dict[str, Any]]:
        """Obtém métricas de técnicos."""
        correlation_id = context.correlation_id if context else None

        try:
            # Obter lista de técnicos
            technicians_data = await self._get_technicians_list(technician_id, correlation_id)

            # Para cada técnico, obter suas métricas
            technician_metrics = []

            for technician in technicians_data:
                tech_id = technician.get("id")
                if not tech_id:
                    continue

                # Criar filtro específico para o técnico
                tech_filter = filters.copy() if filters else MetricsFilterDTO()
                tech_filter.technician_id = tech_id

                # Obter tickets do técnico
                tech_tickets = await self._get_technician_tickets(tech_id, tech_filter, correlation_id)

                # Processar métricas
                metrics = self._process_technician_metrics(technician, tech_tickets, correlation_id)

                technician_metrics.append(metrics)

            # Ordenar por total de tickets (descendente)
            technician_metrics.sort(key=lambda x: x.get("total", 0), reverse=True)

            # Aplicar limite se especificado
            if filters and filters.limit:
                technician_metrics = technician_metrics[: filters.limit]

            return technician_metrics

        except Exception as e:
            self.logger.error(
                f"Erro ao obter métricas de técnicos: {str(e)}",
                extra={"correlation_id": correlation_id},
            )
            raise

    async def get_ticket_metrics(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> Dict[str, Any]:
        """Obtém métricas de tickets."""
        correlation_id = context.correlation_id if context else None

        try:
            # Construir parâmetros da consulta
            params = self._build_ticket_query_params(filters)

            # Obter tickets
            tickets_data = await self.api_client.make_request(endpoint="Ticket", params=params, correlation_id=correlation_id)

            # Processar métricas gerais
            metrics = self._process_ticket_metrics(tickets_data, filters, correlation_id)

            return metrics

        except Exception as e:
            self.logger.error(
                f"Erro ao obter métricas de tickets: {str(e)}",
                extra={"correlation_id": correlation_id},
            )
            raise

    async def get_technician_hierarchy(self, context: Optional[QueryContext] = None) -> Dict[int, str]:
        """Obtém mapeamento de técnico para nível hierárquico."""
        correlation_id = context.correlation_id if context else None

        # Verificar cache
        if self._is_hierarchy_cache_valid():
            if self._technician_hierarchy_cache is None:
                raise GLPIAPIError("Cache de hierarquia inválido")
            return self._technician_hierarchy_cache

        try:
            # Obter usuários/técnicos do GLPI
            users_data = await self.api_client.make_request(
                endpoint="User",
                params={
                    "range": "0-9999",  # Limite alto para pegar todos
                    "is_active": 1,
                    "expand_dropdowns": True,
                },
                correlation_id=correlation_id,
            )

            # Processar hierarquia
            hierarchy = self._process_technician_hierarchy(users_data, correlation_id)

            # Atualizar cache
            self._technician_hierarchy_cache = hierarchy
            self._hierarchy_cache_expires_at = datetime.now() + timedelta(hours=1)

            return hierarchy

        except Exception as e:
            self.logger.error(
                f"Erro ao obter hierarquia de técnicos: {str(e)}",
                extra={"correlation_id": correlation_id},
            )
            raise

    def _is_hierarchy_cache_valid(self) -> bool:
        """Verifica se o cache de hierarquia é válido."""
        return (
            self._technician_hierarchy_cache is not None
            and self._hierarchy_cache_expires_at is not None
            and datetime.now() < self._hierarchy_cache_expires_at
        )

    def _build_ticket_query_params(self, filters: Optional[MetricsFilterDTO]) -> Dict[str, Any]:
        """Constrói parâmetros de consulta para tickets."""
        params = {
            "range": "0-9999",  # Limite alto por padrão
            "expand_dropdowns": True,
            "with_devices": True,
        }

        if not filters:
            return params

        # Filtros de data
        if filters.start_date:
            params["date_creation_start"] = f">={filters.start_date.strftime('%Y-%m-%d %H:%M:%S')}"

        if filters.end_date:
            params["date_creation_end"] = f"<={filters.end_date.strftime('%Y-%m-%d %H:%M:%S')}"

        # Filtro de status
        if filters.status:
            status_map = {
                "novo": 1,
                "pendente": 4,
                "progresso": 2,
                "resolvido": 5,
                "fechado": 6,
                "cancelado": 3,
            }
            status_key = filters.status.lower() if isinstance(filters.status, str) else str(filters.status)
            if status_key in status_map:
                params["status"] = status_map[status_key]

        # Filtro de técnico
        if filters.technician_id:
            params["users_id_assign"] = filters.technician_id

        # Filtro de categoria
        if filters.category_id:
            params["itilcategories_id"] = filters.category_id

        # Filtro de prioridade
        if filters.priority:
            params["priority"] = filters.priority

        # Limite e offset
        if filters.limit:
            end_range = min(filters.limit - 1, 9999)
            start_range = filters.offset or 0
            params["range"] = f"{start_range}-{start_range + end_range}"

        return params

    def _process_tickets_by_hierarchy(
        self,
        tickets_data: Dict[str, Any],
        technician_hierarchy: Dict[int, str],
        correlation_id: Optional[str],
    ) -> Dict[str, Dict[str, Any]]:
        """Processa tickets agrupados por hierarquia."""

        # Inicializar contadores por nível
        levels = {
            "N1": {
                "total": 0,
                "new": 0,
                "pending": 0,
                "in_progress": 0,
                "resolved": 0,
                "closed": 0,
                "cancelled": 0,
            },
            "N2": {
                "total": 0,
                "new": 0,
                "pending": 0,
                "in_progress": 0,
                "resolved": 0,
                "closed": 0,
                "cancelled": 0,
            },
            "N3": {
                "total": 0,
                "new": 0,
                "pending": 0,
                "in_progress": 0,
                "resolved": 0,
                "closed": 0,
                "cancelled": 0,
            },
            "N4": {
                "total": 0,
                "new": 0,
                "pending": 0,
                "in_progress": 0,
                "resolved": 0,
                "closed": 0,
                "cancelled": 0,
            },
        }

        tickets = tickets_data if isinstance(tickets_data, list) else []

        for ticket in tickets:
            # Obter técnico responsável
            tech_id = ticket.get("users_id_assign")
            if not tech_id:
                continue

            # Obter nível do técnico
            tech_level = technician_hierarchy.get(tech_id, "UNKNOWN")
            if tech_level not in levels:
                continue

            # Incrementar contadores
            levels[tech_level]["total"] += 1

            # Mapear status
            status = ticket.get("status", 1)
            status_map = {
                1: "new",
                2: "in_progress",
                3: "cancelled",
                4: "pending",
                5: "resolved",
                6: "closed",
            }

            status_key = status_map.get(status, "new")
            if status_key in levels[tech_level]:
                levels[tech_level][status_key] += 1

        return levels

    async def _get_technicians_list(self, technician_id: Optional[int], correlation_id: Optional[str]) -> List[Dict[str, Any]]:
        """Obtém lista de técnicos."""

        if technician_id:
            # Obter técnico específico
            user_data = await self.api_client.make_request(endpoint=f"User/{technician_id}", correlation_id=correlation_id)
            return [user_data] if user_data else []
        else:
            # Obter todos os técnicos ativos
            users_data = await self.api_client.make_request(
                endpoint="User",
                params={"range": "0-999", "is_active": 1, "expand_dropdowns": True},
                correlation_id=correlation_id,
            )
            return users_data if isinstance(users_data, list) else []

    async def _get_technician_tickets(
        self,
        technician_id: int,
        filters: MetricsFilterDTO,
        correlation_id: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Obtém tickets de um técnico específico."""

        params = self._build_ticket_query_params(filters)
        params["users_id_assign"] = technician_id

        tickets_data = await self.api_client.make_request(endpoint="Ticket", params=params, correlation_id=correlation_id)

        return tickets_data if isinstance(tickets_data, list) else []

    def _process_technician_metrics(
        self,
        technician: Dict[str, Any],
        tickets: List[Dict[str, Any]],
        correlation_id: Optional[str],
    ) -> Dict[str, Any]:
        """Processa métricas de um técnico."""

        metrics = {
            "id": technician.get("id"),
            "name": technician.get("realname", "Desconhecido"),
            "total": len(tickets),
            "new": 0,
            "pending": 0,
            "in_progress": 0,
            "resolved": 0,
            "closed": 0,
            "cancelled": 0,
        }

        # Contar por status
        for ticket in tickets:
            status = ticket.get("status", 1)
            if status == 1:
                metrics["new"] += 1
            elif status == 2:
                metrics["in_progress"] += 1
            elif status == 3:
                metrics["cancelled"] += 1
            elif status == 4:
                metrics["pending"] += 1
            elif status == 5:
                metrics["resolved"] += 1
            elif status == 6:
                metrics["closed"] += 1

        # Calcular tempo médio de resolução (simulado)
        resolved_tickets = [t for t in tickets if t.get("status") == 5]
        if resolved_tickets:
            # Usando valor padrão até implementação completa de cálculo de datas
            metrics["avg_resolution_time"] = 2.5

        # Última atividade
        if tickets:
            latest_ticket = max(tickets, key=lambda t: t.get("date_mod", "1970-01-01"))
            metrics["last_activity"] = latest_ticket.get("date_mod")

        return metrics

    def _process_ticket_metrics(
        self,
        tickets_data: Dict[str, Any],
        filters: Optional[MetricsFilterDTO],
        correlation_id: Optional[str],
    ) -> Dict[str, Any]:
        """Processa métricas gerais de tickets."""

        tickets = tickets_data if isinstance(tickets_data, list) else []

        # Obter tickets recentes para o dashboard
        recent_tickets = []
        if len(tickets) > 0:
            # Ordenar por data de modificação e pegar os 20 mais recentes
            sorted_tickets = sorted(tickets, key=lambda t: t.get("date_mod", "1970-01-01"), reverse=True)

            for ticket in sorted_tickets[:20]:
                recent_tickets.append(
                    {
                        "id": ticket.get("id"),
                        "title": ticket.get("name", "Sem título"),
                        "status": self._map_ticket_status(ticket.get("status", 1)),
                        "created_at": ticket.get("date_creation"),
                        "technician_id": ticket.get("users_id_assign"),
                    }
                )

        return {"recent_tickets": recent_tickets}

    def _process_technician_hierarchy(self, users_data: Dict[str, Any], correlation_id: Optional[str]) -> Dict[int, str]:
        """Processa hierarquia de técnicos."""

        hierarchy = {}
        users = users_data if isinstance(users_data, list) else []

        for user in users:
            user_id = user.get("id")
            if not user_id:
                continue

            # Determinar nível baseado em grupos, perfis ou outros critérios
            # TODO: Implementar lógica real baseada na estrutura do GLPI
            level = self._determine_user_level(user)
            hierarchy[user_id] = level

        return hierarchy

    def _determine_user_level(self, user: Dict[str, Any]) -> str:
        """Determina o nível hierárquico de um usuário."""
        # TODO: Implementar lógica real baseada em:
        # - Grupos do usuário
        # - Perfis atribuídos
        # - Campos customizados
        # - Localização/entidade

        # Por enquanto, distribuição simulada
        user_id = user.get("id", 0)
        if user_id % 4 == 0:
            return "N4"
        elif user_id % 3 == 0:
            return "N3"
        elif user_id % 2 == 0:
            return "N2"
        else:
            return "N1"

    def _map_ticket_status(self, status_id: int) -> str:
        """Mapeia ID de status para string."""
        status_map = {
            1: "novo",
            2: "progresso",
            3: "cancelado",
            4: "pendente",
            5: "resolvido",
            6: "fechado",
        }
        return status_map.get(status_id, "novo")

    async def get_new_tickets(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> List[Dict[str, Any]]:
        """Obtém tickets novos/recentes do GLPI."""
        correlation_id = context.correlation_id if context else None

        try:
            # Descobrir field IDs primeiro para queries corretas
            field_ids = await self.discover_field_ids(context)

            # Construir parâmetros para search API
            params = self._build_search_params_for_new_tickets(filters, field_ids)

            # Fazer requisição para tickets via search endpoint
            tickets_response = await self.api_client.make_request(
                endpoint="search/Ticket", params=params, correlation_id=correlation_id
            )

            # Processar resposta no formato search API
            return self._process_search_tickets_response(tickets_response, correlation_id)

        except Exception as e:
            self.logger.error(
                f"Erro ao obter tickets novos: {str(e)}",
                extra={"correlation_id": correlation_id},
            )
            raise

    async def get_system_status(self, context: Optional[QueryContext] = None) -> Dict[str, Any]:
        """Obtém status do sistema GLPI."""
        correlation_id = context.correlation_id if context else None

        try:
            # Verificar status da sessão - usar endpoint simples que sempre funciona
            start_time = time.time()
            session_response = await self.api_client.make_request(
                endpoint="getMyProfiles", params={}, correlation_id=correlation_id
            )
            response_time = (time.time() - start_time) * 1000

            # Processar status
            return self._process_system_status(session_response, response_time, correlation_id)

        except Exception as e:
            self.logger.error(
                f"Erro ao obter status do sistema: {str(e)}",
                extra={"correlation_id": correlation_id},
            )
            # Retornar status básico em caso de erro
            return {
                "api_status": "error",
                "error_message": str(e),
                "last_check": datetime.now().isoformat(),
                "health_score": 0.0,
            }

    async def discover_field_ids(self, context: Optional[QueryContext] = None) -> Dict[str, int]:
        """Descobre IDs dos campos GLPI."""
        correlation_id = context.correlation_id if context else None

        try:
            # Obter opções de busca para tickets
            search_options = await self.api_client.make_request(
                endpoint="listSearchOptions/Ticket", params={}, correlation_id=correlation_id
            )

            # Processar e mapear campos
            return self._process_field_discovery(search_options, correlation_id)

        except Exception as e:
            self.logger.error(
                f"Erro ao descobrir IDs dos campos: {str(e)}",
                extra={"correlation_id": correlation_id},
            )
            # Retornar mapeamento padrão conhecido
            return {
                "group_id": 71,
                "status_id": 12,
                "priority_id": 3,
                "category_id": 5,
                "technician_id": 4,
                "requester_id": 22,
                "location_id": 83,
                "created_date": 15,
                "updated_date": 19,
                "title": 1,
                "description": 21,
            }

    def _build_search_params_for_new_tickets(
        self, filters: Optional[MetricsFilterDTO], field_ids: Dict[str, int]
    ) -> Dict[str, Any]:
        """Constrói parâmetros para search API de tickets novos."""
        params = {
            "range": "0-50",  # Limite para tickets novos
        }

        # Forçar colunas necessárias
        params["forcedisplay[0]"] = field_ids.get("title", 1)  # Name/title
        params["forcedisplay[1]"] = field_ids.get("status_id", 12)  # Status
        params["forcedisplay[2]"] = field_ids.get("created_date", 15)  # Date creation
        params["forcedisplay[3]"] = field_ids.get("updated_date", 19)  # Date modification
        params["forcedisplay[4]"] = field_ids.get("priority_id", 3)  # Priority
        params["forcedisplay[5]"] = field_ids.get("technician_id", 4)  # Technician
        params["forcedisplay[6]"] = field_ids.get("description", 21)  # Content

        criteria_idx = 0

        # Filtro de status - se não especificado, usar "novo"
        if not filters or not filters.status:
            status_value = "1"  # Status novo
        else:
            # Mapear status string para valor
            status_map = {
                "novo": "1",
                "pendente": "4",
                "progresso": "2",
                "resolvido": "5",
                "fechado": "6",
                "cancelado": "3",
            }
            status_value = status_map.get(filters.status.lower(), "1")

        params[f"criteria[{criteria_idx}][field]"] = str(field_ids.get("status_id", 12))
        params[f"criteria[{criteria_idx}][searchtype]"] = "equals"
        params[f"criteria[{criteria_idx}][value]"] = status_value
        criteria_idx += 1

        # Filtros de data
        if filters:
            if filters.start_date:
                params[f"criteria[{criteria_idx}][field]"] = str(field_ids.get("created_date", 15))
                params[f"criteria[{criteria_idx}][searchtype]"] = "morethan"
                params[f"criteria[{criteria_idx}][value]"] = filters.start_date.strftime("%Y-%m-%d %H:%M:%S")
                criteria_idx += 1

            if filters.end_date:
                params[f"criteria[{criteria_idx}][field]"] = str(field_ids.get("created_date", 15))
                params[f"criteria[{criteria_idx}][searchtype]"] = "lessthan"
                params[f"criteria[{criteria_idx}][value]"] = filters.end_date.strftime("%Y-%m-%d %H:%M:%S")
                criteria_idx += 1

            if filters.limit:
                params["range"] = f"0-{min(filters.limit, 100)}"

        # Ordenar por data de criação (mais recentes primeiro)
        params["sort"] = str(field_ids.get("created_date", 15))
        params["order"] = "DESC"

        return params

    def _process_search_tickets_response(
        self, search_response: Dict[str, Any], correlation_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Processa resposta da search API do GLPI."""
        processed_tickets = []

        try:
            # Search API retorna: {columns: [field_ids], data: [[row_values]]}
            columns = search_response.get("columns", [])
            data_rows = search_response.get("data", [])

            if not columns or not data_rows:
                return []

            # Criar mapeamento de colunas para índices
            col_map = {str(col): idx for idx, col in enumerate(columns)}

            for row in data_rows:
                try:
                    processed_ticket = {
                        "id": self._get_col_value(row, col_map, "1", ""),  # ID is usually field 1
                        "title": self._get_col_value(row, col_map, "1", "Sem título"),  # Name/title
                        "description": self._get_col_value(row, col_map, "21", ""),  # Content
                        "status": self._map_ticket_status(int(self._get_col_value(row, col_map, "12", 1))),  # Status
                        "priority": int(self._get_col_value(row, col_map, "3", 3)),  # Priority
                        "technician_id": self._get_col_value(row, col_map, "4", None),  # Technician
                        "created_at": self._parse_glpi_datetime(
                            self._get_col_value(row, col_map, "15", None)
                        ),  # Date creation
                        "updated_at": self._parse_glpi_datetime(self._get_col_value(row, col_map, "19", None)),  # Date mod
                        "category": None,  # Not included in forcedisplay
                        "requester": None,  # Not included in forcedisplay
                        "location": None,  # Not included in forcedisplay
                    }
                    processed_tickets.append(processed_ticket)

                except Exception as e:
                    self.logger.warning(
                        f"Erro ao processar linha de ticket: {str(e)}, row: {row}",
                        extra={"correlation_id": correlation_id},
                    )
                    continue

        except Exception as e:
            self.logger.error(
                f"Erro ao processar resposta de search: {str(e)}",
                extra={"correlation_id": correlation_id},
            )

        return processed_tickets

    def _get_col_value(self, row: List[Any], col_map: Dict[str, int], field_id: str, default: Any) -> Any:
        """Extrai valor de coluna da linha de dados."""
        col_idx = col_map.get(field_id)
        if col_idx is not None and col_idx < len(row):
            return row[col_idx]
        return default

    def _process_new_tickets(self, tickets_data: List[Dict[str, Any]], correlation_id: Optional[str]) -> List[Dict[str, Any]]:
        """Processa dados de tickets novos."""
        processed_tickets = []

        for ticket in tickets_data:
            try:
                processed_ticket = {
                    "id": ticket.get("id"),
                    "title": ticket.get("name", "Sem título"),
                    "description": ticket.get("content", ""),
                    "status": self._map_ticket_status(ticket.get("status", 1)),
                    "priority": ticket.get("priority", 3),
                    "category": ticket.get("itilcategories_id"),
                    "technician_id": ticket.get("users_id_tech"),
                    "created_at": self._parse_glpi_datetime(ticket.get("date")),
                    "updated_at": self._parse_glpi_datetime(ticket.get("date_mod")),
                    "requester": ticket.get("users_id_requester"),
                    "location": ticket.get("locations_id"),
                }
                processed_tickets.append(processed_ticket)

            except Exception as e:
                self.logger.warning(
                    f"Erro ao processar ticket {ticket.get('id', 'unknown')}: {str(e)}",
                    extra={"correlation_id": correlation_id},
                )
                continue

        return processed_tickets

    def _process_system_status(
        self, session_data: Dict[str, Any], response_time: float, correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Processa dados de status do sistema."""
        try:
            return {
                "glpi_version": "10.0.x",  # Seria obtido de config endpoint
                "api_version": "1.0",
                "database_status": "connected" if session_data else "disconnected",
                "api_status": "healthy",
                "last_check": datetime.now().isoformat(),
                "response_time_ms": response_time,
                "active_sessions": len(session_data.get("myprofiles", [])) if session_data else 0,
                "services": {
                    "web_server": "running",
                    "database": "running" if session_data else "error",
                    "api": "running",
                },
                "health_score": 90.0 if session_data else 50.0,
            }

        except Exception as e:
            self.logger.warning(
                f"Erro ao processar status do sistema: {str(e)}",
                extra={"correlation_id": correlation_id},
            )
            return {
                "api_status": "partial",
                "error_message": str(e),
                "last_check": datetime.now().isoformat(),
                "health_score": 70.0,
            }

    def _process_field_discovery(self, search_options: Dict[str, Any], correlation_id: Optional[str]) -> Dict[str, int]:
        """Processa opções de busca para descobrir IDs dos campos."""
        field_mapping = {}

        try:
            # GLPI retorna as opções de busca em formato diferente dependendo da versão
            # Tentar diferentes estruturas de resposta
            options = search_options
            if isinstance(search_options, dict) and "options" in search_options:
                options = search_options["options"]

            # Mapeamento de nomes conhecidos para IDs
            for field_id, field_info in options.items():
                if isinstance(field_info, dict):
                    field_name = field_info.get("name", "").lower()

                    # Mapear campos conhecidos
                    if "group" in field_name or "assign" in field_name:
                        field_mapping["group_id"] = int(field_id)
                    elif "status" in field_name:
                        field_mapping["status_id"] = int(field_id)
                    elif "priority" in field_name:
                        field_mapping["priority_id"] = int(field_id)
                    elif "category" in field_name:
                        field_mapping["category_id"] = int(field_id)
                    elif "tech" in field_name or "assigned" in field_name:
                        field_mapping["technician_id"] = int(field_id)
                    elif "requester" in field_name or "user" in field_name:
                        field_mapping["requester_id"] = int(field_id)
                    elif "location" in field_name:
                        field_mapping["location_id"] = int(field_id)
                    elif "date" in field_name and "creation" in field_name:
                        field_mapping["created_date"] = int(field_id)
                    elif "title" in field_name or "name" in field_name:
                        field_mapping["title"] = int(field_id)
                    elif "description" in field_name or "content" in field_name:
                        field_mapping["description"] = int(field_id)

        except Exception as e:
            self.logger.warning(
                f"Erro ao processar descoberta de campos: {str(e)}",
                extra={"correlation_id": correlation_id},
            )

        # Adicionar campos padrão se não foram descobertos
        default_mapping = {
            "group_id": 71,
            "status_id": 12,
            "priority_id": 3,
            "category_id": 5,
            "technician_id": 4,
            "requester_id": 22,
            "location_id": 83,
            "created_date": 15,
            "title": 1,
            "description": 21,
        }

        for key, default_value in default_mapping.items():
            if key not in field_mapping:
                field_mapping[key] = default_value

        return field_mapping

    def _parse_glpi_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Converte string de data do GLPI para datetime."""
        if not date_str:
            return None

        try:
            # GLPI geralmente usa formato YYYY-MM-DD HH:MM:SS
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            # Fallback para ISO format
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return None

    async def close(self) -> None:
        """Fecha conexões e limpa recursos."""
        self.session_manager.close_session()  # Remove await - método é síncrono
        self._technician_hierarchy_cache = None
        self._hierarchy_cache_expires_at = None


# Factory para criação do adapter
def create_glpi_metrics_adapter(*args, **kwargs) -> GLPIMetricsAdapter:
    """
    Cria instância do GLPIMetricsAdapter.

    Tolerante a diferentes estilos de chamada:
    - create_glpi_metrics_adapter(config)  # GLPIConfig object
    - create_glpi_metrics_adapter(base_url, app_token, user_token, **kwargs)
    - create_glpi_metrics_adapter(base_url="...", app_token="...", user_token="...", **kwargs)
    """
    logger = logging.getLogger(__name__)

    # Se primeiro argumento é GLPIConfig, use-o diretamente
    if args and isinstance(args[0], GLPIConfig):
        if len(args) > 1 or kwargs:
            logger.warning("GLPIConfig provided but additional args/kwargs ignored: %s %s", args[1:], kwargs)
        return GLPIMetricsAdapter(args[0])

    # Resolve parâmetros de diferentes fontes
    base_url = args[0] if len(args) > 0 else kwargs.pop("base_url", None)
    app_token = args[1] if len(args) > 1 else kwargs.pop("app_token", None)
    user_token = args[2] if len(args) > 2 else kwargs.pop("user_token", None)

    # Validar parâmetros obrigatórios
    if not all([base_url, app_token, user_token]):
        raise ValueError(
            f"Missing required parameters: base_url={base_url}, app_token={bool(app_token)}, user_token={bool(user_token)}"
        )

    # Log warning se parâmetros duplicados foram detectados
    duplicate_params = []
    if "base_url" in kwargs:
        duplicate_params.append("base_url")
        kwargs.pop("base_url")
    if "app_token" in kwargs:
        duplicate_params.append("app_token")
        kwargs.pop("app_token")
    if "user_token" in kwargs:
        duplicate_params.append("user_token")
        kwargs.pop("user_token")

    if duplicate_params:
        logger.warning("Duplicate parameters resolved: %s", duplicate_params)

    config = GLPIConfig(base_url=base_url, app_token=app_token, user_token=user_token, **kwargs)
    return GLPIMetricsAdapter(config)


# Exemplo de uso
async def example_usage():
    """Exemplo de como usar o GLPIMetricsAdapter."""

    # Criar adapter
    adapter = create_glpi_metrics_adapter(
        base_url="https://glpi.example.com",
        app_token="your-app-token",
        user_token="your-user-token",
    )

    try:
        # Criar contexto
        from ....application.queries.metrics_query import QueryContext

        context = QueryContext(correlation_id="example-123")

        # Obter métricas por hierarquia
        hierarchy_metrics = await adapter.get_ticket_count_by_hierarchy(context=context)
        print(f"Métricas por hierarquia: {hierarchy_metrics}")

        # Obter ranking de técnicos
        technician_metrics = await adapter.get_technician_metrics(context=context)
        print(f"Top técnico: {technician_metrics[0]['name'] if technician_metrics else 'Nenhum'}")

    finally:
        # Fechar conexões
        await adapter.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
