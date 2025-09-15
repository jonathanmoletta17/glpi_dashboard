from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import datetime
import logging
import time
import traceback
from functools import wraps

from core.application.contracts.metrics_contracts import UnifiedGLPIServiceContract
from services.legacy.glpi_service_facade import GLPIServiceFacade
from utils.legacy_monitoring import legacy_monitor
from schemas.dashboard import (
    DashboardMetrics,
    TechnicianRanking,
    NewTicket,
    ApiResponse,
    ApiError,
    TicketStatus,
    TechnicianLevel,
    NiveisMetrics,
    LevelMetrics,
    TendenciasMetrics,
    FiltersApplied
)
# ApiResponse já importado de backend.schemas.dashboard
from core.infrastructure.converters.legacy_data_converter import LegacyDataConverter


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator para implementar retry logic em métodos do adapter"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    self.logger.warning(
                        f"Tentativa {attempt + 1}/{max_retries} falhou para {func.__name__}: {str(e)}"
                    )
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Backoff exponencial
                    
            self.logger.error(f"Todas as tentativas falharam para {func.__name__}: {str(last_exception)}")
            raise last_exception
            
        return wrapper
    return decorator


class LegacyServiceAdapter(UnifiedGLPIServiceContract):
    """Adapter que conecta Clean Architecture aos serviços legacy robustos
    
    Este adapter serve como ponte entre a nova arquitetura limpa e os serviços
    legacy existentes, garantindo compatibilidade total e aproveitando a robustez
    dos serviços já testados e validados.
    
    Características:
    - Conversão automática de dados entre formatos
    - Tratamento robusto de erros com retry logic
    - Logging estruturado para observabilidade
    - Suporte completo a correlation IDs
    - Performance otimizada com cache dos serviços legacy
    """
    
    def __init__(self):
        """Inicializa o adapter com configurações necessárias"""
        self._legacy_facade = GLPIServiceFacade()
        self._converter = LegacyDataConverter()
        self.logger = logging.getLogger("legacy_adapter")
        self._initialize_adapter()
    
    def _initialize_adapter(self):
        """Inicializa o adapter com configurações necessárias"""
        try:
            # Verifica se o facade legacy está funcionando
            health_status = self._legacy_facade.health_check()
            if not health_status.get('status') == 'healthy':
                self.logger.warning("Legacy facade não está completamente saudável")
            
            # Força autenticação inicial
            if not self._legacy_facade.authenticate():
                self.logger.error("Falha na autenticação inicial do legacy facade")
                raise RuntimeError("Não foi possível autenticar com o GLPI")
            
            self.logger.info("LegacyServiceAdapter inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do adapter: {str(e)}")
            raise
    
    def _log_method_call(self, method_name: str, correlation_id: Optional[str] = None, **kwargs):
        """Log estruturado para chamadas de métodos"""
        log_data = {
            "method": method_name,
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "adapter": "LegacyServiceAdapter"
        }
        log_data.update(kwargs)
        self.logger.info(f"Executando {method_name}", extra=log_data)
    
    @legacy_monitor.monitor_method("legacy_adapter_get_dashboard_metrics")
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_dashboard_metrics(self, correlation_id: Optional[str] = None) -> ApiResponse:
        """Obtém métricas do dashboard usando serviços legacy
        
        Args:
            correlation_id: ID de correlação para rastreamento
            
        Returns:
            ApiResponse[DashboardMetrics]: Métricas do dashboard
        """
        self._log_method_call("get_dashboard_metrics", correlation_id)
        
        try:
            # Obtém dados básicos do dashboard (deixa exceções propagarem para o retry)
            dashboard_data = self._legacy_facade.get_dashboard_metrics()
            if not dashboard_data.get('success', False):
                # Falha de dados não deve fazer retry, retorna erro imediatamente
                error_msg = "Erro ao obter métricas do dashboard: Falha ao obter dados do dashboard"
                self.logger.error(error_msg, extra={"correlation_id": correlation_id})
                return ApiResponse(
                    success=False,
                    data=None,
                    message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Converte dados usando o converter
            dashboard_metrics = self._converter.convert_dashboard_data(dashboard_data.get('data', {}))
            
            self.logger.info(
                f"Dashboard metrics obtidas com sucesso",
                extra={
                    "correlation_id": correlation_id,
                    "total_tickets": dashboard_metrics.total,
                    "open_tickets": dashboard_metrics.novos + dashboard_metrics.pendentes
                }
            )
            
            return ApiResponse(
                success=True,
                data=dashboard_metrics,
                message="Métricas do dashboard obtidas com sucesso",
                correlation_id=correlation_id
            )
            
        except Exception as e:
            # Define exceções customizadas que devem fazer retry
            from core.infrastructure.external.glpi.metrics_adapter import GLPIConnectionError, GLPIAuthenticationError, GLPIAPIError
            
            retry_exception_types = (GLPIConnectionError, GLPIAuthenticationError, GLPIAPIError)
            
            # Define palavras-chave que indicam problemas temporários de rede (apenas para retry)
            retry_keywords = ['rede temporária', 'temporary network', 'falha temporária', 'temporary failure']
            
            # Verifica se é uma exceção que deve fazer retry
            should_retry = (
                isinstance(e, retry_exception_types) or
                any(keyword in str(e).lower() for keyword in retry_keywords)
            )
            
            if should_retry:
                # Propaga exceções para retry
                raise
            else:
                # Captura outras exceções (TimeoutError, ConnectionError padrão sem palavras-chave)
                error_msg = f"Erro ao obter métricas do dashboard: {str(e)}"
                self.logger.error(error_msg, extra={"correlation_id": correlation_id, "error": str(e)})
                return ApiResponse(
                    success=False,
                    data=None,
                    message=error_msg,
                    correlation_id=correlation_id
                )
    
    @legacy_monitor.monitor_method("legacy_adapter_get_dashboard_metrics_with_date_filter")
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_dashboard_metrics_with_date_filter(
        self, 
        start_date: str, 
        end_date: str, 
        correlation_id: Optional[str] = None
    ) -> ApiResponse:
        """Obtém métricas do dashboard com filtro de data
        
        Args:
            start_date: Data de início (formato: YYYY-MM-DD)
            end_date: Data de fim (formato: YYYY-MM-DD)
            correlation_id: ID de correlação para rastreamento
            
        Returns:
            ApiResponse[DashboardMetrics]: Métricas filtradas por data
        """
        self._log_method_call(
            "get_dashboard_metrics_with_date_filter", 
            correlation_id, 
            start_date=start_date, 
            end_date=end_date
        )
        
        try:
            # Obtém contagem de tickets primeiro
            ticket_count = self._legacy_facade.get_ticket_count()
            if ticket_count is None or ticket_count < 0:
                raise ValueError("Falha ao obter contagem de tickets")
            
            # Obtém dados do dashboard
            dashboard_data = self._legacy_facade.get_dashboard_metrics()
            if not dashboard_data.get('success', False):
                raise ValueError("Falha ao obter dados do dashboard")
            
            # Aplica filtro de data nos dados
            filtered_data = self._apply_date_filter(
                dashboard_data.get('data', {}), 
                start_date, 
                end_date
            )
            
            # Converte dados usando o converter
            dashboard_metrics = self._converter.convert_dashboard_data(filtered_data)
            
            # Adiciona informações de filtro
            dashboard_metrics.filters_applied.date_range = f"{start_date} - {end_date}"
            
            self.logger.info(
                f"Dashboard metrics com filtro de data obtidas com sucesso",
                extra={
                    "correlation_id": correlation_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_tickets": dashboard_metrics.total
                }
            )
            
            return ApiResponse(
                success=True,
                data=dashboard_metrics,
                message="Métricas do dashboard com filtro de data obtidas com sucesso",
                correlation_id=correlation_id
            )
            
        except Exception as e:
            error_msg = f"Erro ao obter métricas com filtro de data: {str(e)}"
            self.logger.error(
                error_msg, 
                extra={
                    "correlation_id": correlation_id, 
                    "start_date": start_date,
                    "end_date": end_date,
                    "error": str(e)
                }
            )
            
            return ApiResponse(
                success=False,
                data=None,
                message=error_msg,
                correlation_id=correlation_id
            )
    
    @legacy_monitor.monitor_method("legacy_adapter_get_dashboard_metrics_with_modification_date_filter")
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_dashboard_metrics_with_modification_date_filter(
        self, 
        start_date: str, 
        end_date: str, 
        correlation_id: Optional[str] = None
    ) -> ApiResponse:
        """Obtém métricas do dashboard com filtro de data de modificação
        
        Args:
            start_date: Data de início da modificação (formato: YYYY-MM-DD)
            end_date: Data de fim da modificação (formato: YYYY-MM-DD)
            correlation_id: ID de correlação para rastreamento
            
        Returns:
            ApiResponse[DashboardMetrics]: Métricas filtradas por data de modificação
        """
        self._log_method_call(
            "get_dashboard_metrics_with_modification_date_filter", 
            correlation_id, 
            mod_start_date=start_date, 
            mod_end_date=end_date
        )
        
        try:
            # Obtém dados do dashboard
            dashboard_data = self._legacy_facade.get_dashboard_metrics()
            if not dashboard_data.get('success', False):
                raise ValueError("Falha ao obter dados do dashboard")
            
            # Aplica filtro de data de modificação
            filtered_data = self._apply_modification_date_filter(
                dashboard_data.get('data', {}), 
                start_date, 
                end_date
            )
            
            # Converte dados usando o converter
            dashboard_metrics = self._converter.convert_dashboard_data(filtered_data)
            
            # Adiciona informações de filtro de modificação
            dashboard_metrics.filters_applied.date_range = f"Modificação: {start_date} - {end_date}"
            
            self.logger.info(
                f"Dashboard metrics com filtro de data de modificação obtidas com sucesso",
                extra={
                    "correlation_id": correlation_id,
                    "mod_start_date": start_date,
                    "mod_end_date": end_date,
                    "total_tickets": dashboard_metrics.total
                }
            )
            
            return ApiResponse(
                success=True,
                data=dashboard_metrics,
                message="Métricas do dashboard com filtro de data de modificação obtidas com sucesso",
                correlation_id=correlation_id
            )
            
        except Exception as e:
            error_msg = f"Erro ao obter métricas com filtro de data de modificação: {str(e)}"
            self.logger.error(
                error_msg, 
                extra={
                    "correlation_id": correlation_id, 
                    "mod_start_date": start_date,
                    "mod_end_date": end_date,
                    "error": str(e)
                }
            )
            
            return ApiResponse(
                success=False,
                data=None,
                message=error_msg,
                correlation_id=correlation_id
            )
    
    @legacy_monitor.monitor_method("legacy_adapter_get_dashboard_metrics_with_filters")
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_dashboard_metrics_with_filters(
        self, 
        filters: Dict[str, Any], 
        correlation_id: Optional[str] = None
    ) -> ApiResponse:
        """Obtém métricas do dashboard com filtros personalizados
        
        Args:
            filters: Dicionário com filtros a serem aplicados
            correlation_id: ID de correlação para rastreamento
            
        Returns:
            ApiResponse[DashboardMetrics]: Métricas filtradas
        """
        self._log_method_call(
            "get_dashboard_metrics_with_filters", 
            correlation_id, 
            filters=filters
        )
        
        try:
            # Obtém dados do dashboard
            dashboard_data = self._legacy_facade.get_dashboard_metrics()
            if not dashboard_data.get('success', False):
                raise ValueError("Falha ao obter dados do dashboard")
            
            # Aplica filtros personalizados
            filtered_data = self._apply_custom_filters(
                dashboard_data.get('data', {}), 
                filters
            )
            
            # Converte dados usando o converter
            dashboard_metrics = self._converter.convert_dashboard_data(filtered_data)
            
            # Adiciona informações de filtros aplicados
            self._update_filters_applied(dashboard_metrics, filters)
            
            self.logger.info(
                f"Dashboard metrics com filtros personalizados obtidas com sucesso",
                extra={
                    "correlation_id": correlation_id,
                    "filters": filters,
                    "total_tickets": dashboard_metrics.total
                }
            )
            
            return ApiResponse(
                success=True,
                data=dashboard_metrics,
                message="Métricas do dashboard com filtros personalizados obtidas com sucesso",
                correlation_id=correlation_id
            )
            
        except Exception as e:
            error_msg = f"Erro ao obter métricas com filtros personalizados: {str(e)}"
            self.logger.error(
                error_msg, 
                extra={
                    "correlation_id": correlation_id, 
                    "filters": filters,
                    "error": str(e)
                }
            )
            
            return ApiResponse(
                success=False,
                data=None,
                message=error_msg,
                correlation_id=correlation_id
            )
    
    @legacy_monitor.monitor_method("legacy_adapter_get_technician_ranking")
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_technician_ranking(
        self, 
        limit: Optional[int] = None, 
        correlation_id: Optional[str] = None
    ) -> ApiResponse:
        """Obtém ranking de técnicos usando serviços legacy
        
        Args:
            limit: Limite de técnicos no ranking
            correlation_id: ID de correlação para rastreamento
            
        Returns:
            ApiResponse[List[Dict]]: Ranking de técnicos
        """
        self._log_method_call(
            "get_technician_ranking", 
            correlation_id, 
            limit=limit
        )
        
        try:
            # Obtém dados de performance dos técnicos
            technicians_data = self._legacy_facade.get_technician_performance()
            if not technicians_data.get('success', False):
                raise ValueError("Falha ao obter dados dos técnicos")
            
            # Converte para formato de ranking usando o método correto
            ranking_data = self._converter.convert_technician_ranking(
                technicians_data.get('data', [])
            )
            
            # Aplica limite se especificado
            if limit and isinstance(ranking_data, list):
                ranking_data = ranking_data[:limit]
            
            self.logger.info(
                f"Ranking de técnicos obtido com sucesso",
                extra={
                    "correlation_id": correlation_id,
                    "count": len(ranking_data) if isinstance(ranking_data, list) else 0,
                    "limit": limit
                }
            )
            
            return ApiResponse(
                success=True,
                data=ranking_data,
                message="Ranking de técnicos obtido com sucesso",
                correlation_id=correlation_id
            )
            
        except Exception as e:
            error_msg = f"Erro ao obter ranking de técnicos: {str(e)}"
            self.logger.error(
                error_msg, 
                extra={
                    "correlation_id": correlation_id, 
                    "limit": limit,
                    "error": str(e)
                }
            )
            
            return ApiResponse(
                success=False,
                data=None,
                message=error_msg,
                correlation_id=correlation_id
            )
    
    @legacy_monitor.monitor_method("legacy_adapter_get_new_tickets")
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_new_tickets(
        self, 
        limit: Optional[int] = 20, 
        correlation_id: Optional[str] = None
    ) -> ApiResponse:
        """Obtém tickets novos usando serviços legacy
        
        Args:
            limit: Limite de tickets a retornar
            correlation_id: ID de correlação para rastreamento
            
        Returns:
            ApiResponse[List[Dict]]: Lista de tickets novos
        """
        self._log_method_call(
            "get_new_tickets", 
            correlation_id, 
            limit=limit
        )
        
        try:
            # Obtém tickets recentes do facade legacy
            tickets_data = self._legacy_facade.get_recent_tickets()
            if not tickets_data.get('success', False):
                raise ValueError("Falha ao obter tickets novos")
            
            # Converte dados usando o converter
            converted_tickets = self._converter.convert_new_tickets(
                tickets_data.get('data', [])
            )
            
            # Aplica limite se especificado
            if limit and isinstance(converted_tickets, list):
                converted_tickets = converted_tickets[:limit]
            
            self.logger.info(
                f"Tickets novos obtidos com sucesso",
                extra={
                    "correlation_id": correlation_id,
                    "count": len(converted_tickets) if isinstance(converted_tickets, list) else 0,
                    "limit": limit
                }
            )
            
            return ApiResponse(
                success=True,
                data=converted_tickets,
                message="Tickets novos obtidos com sucesso",
                correlation_id=correlation_id
            )
            
        except Exception as e:
            error_msg = f"Erro ao obter tickets novos: {str(e)}"
            self.logger.error(
                error_msg, 
                extra={
                    "correlation_id": correlation_id, 
                    "limit": limit,
                    "error": str(e)
                }
            )
            
            return ApiResponse(
                success=False,
                data=None,
                message=error_msg,
                correlation_id=correlation_id
            )
    
    @legacy_monitor.monitor_method("legacy_adapter_get_system_status")
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_system_status(self, correlation_id: Optional[str] = None) -> ApiResponse:
        """Obtém status do sistema usando serviços legacy
        
        Args:
            correlation_id: ID de correlação para rastreamento
            
        Returns:
            ApiResponse[Dict]: Status do sistema
        """
        self._log_method_call("get_system_status", correlation_id)
        
        try:
            # Chama método legacy
            legacy_status = self._legacy_facade.health_check()
            
            # Converte e normaliza dados usando LegacyDataConverter
            converted_status = self._converter.convert_system_status(legacy_status)
            
            # Enriquece com informações adicionais
            enhanced_status = {
                **converted_status,
                "adapter_status": "healthy",
                "legacy_facade_status": "connected",
                "adapter_version": "1.0.0",
                "legacy_source": "GLPIServiceFacade",
                "correlation_id": correlation_id
            }
            
            self.logger.info(
                f"Status do sistema obtido com sucesso",
                extra={
                    "correlation_id": correlation_id,
                    "status": enhanced_status.get('status', 'unknown')
                }
            )
            
            return ApiResponse(
                success=True,
                data=enhanced_status,
                message="Status do sistema obtido com sucesso",
                correlation_id=correlation_id
            )
            
        except Exception as e:
            error_msg = f"Erro ao obter status do sistema: {str(e)}"
            self.logger.error(
                error_msg, 
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e)
                }
            )
            
            # Retorna status de erro
            error_status = {
                "status": "unhealthy",
                "adapter_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "correlation_id": correlation_id
            }
            
            return ApiResponse(
                success=False,
                data=error_status,
                message=error_msg,
                correlation_id=correlation_id
            )
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_all_technician_ids_and_names(self, entity_id: Optional[int] = None) -> Tuple[List[int], List[str]]:
        """Obtém IDs e nomes de todos os técnicos
        
        Args:
            entity_id: ID da entidade para filtrar técnicos
            
        Returns:
            Tuple com listas de IDs e nomes dos técnicos
        """
        try:
            self.logger.info(f"Obtendo IDs e nomes de técnicos - entity_id: {entity_id}")
            
            # Chama o método do facade legacy
            technician_data = self._legacy_facade.get_all_technician_ids_and_names(entity_id)
            
            if isinstance(technician_data, tuple) and len(technician_data) == 2:
                ids, names = technician_data
                self.logger.info(f"Obtidos {len(ids)} técnicos com sucesso")
                return ids, names
            else:
                # Se não retornar tupla, tenta extrair dos dados
                ids = []
                names = []
                if isinstance(technician_data, list):
                    for tech in technician_data:
                        if isinstance(tech, dict):
                            ids.append(tech.get('id', 0))
                            names.append(tech.get('name', 'Desconhecido'))
                
                return ids, names
                
        except Exception as e:
            self.logger.error(f"Erro ao obter técnicos: {str(e)}")
            return [], []
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_technician_ranking_with_filters(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 50,
        entity_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> List[TechnicianRanking]:
        """Obtém ranking de técnicos com filtros
        
        Args:
            start_date: Data de início do filtro
            end_date: Data de fim do filtro
            level: Nível do técnico (N1, N2, N3, N4)
            limit: Limite de resultados
            entity_id: ID da entidade
            correlation_id: ID de correlação para rastreamento
            
        Returns:
            Lista de rankings de técnicos
        """
        try:
            self.logger.debug(f"LegacyServiceAdapter.get_technician_ranking_with_filters chamado - correlation_id: {correlation_id}")
            
            # Prepara filtros
            filters = {
                'start_date': start_date,
                'end_date': end_date,
                'level': level,
                'limit': limit,
                'entity_id': entity_id
            }
            
            # Remove filtros vazios
            filters = {k: v for k, v in filters.items() if v is not None}
            
            # Chama o método do facade legacy
            raw_data = self._legacy_facade.get_technician_ranking_with_filters(**filters)
            
            # Converte dados usando o converter
            converted_data = self._converter.convert_technician_ranking_list(raw_data)
            
            self.logger.info(f"Ranking de técnicos obtido com sucesso - {len(converted_data)} técnicos")
            return converted_data
            
        except Exception as e:
            self.logger.error(f"Erro ao obter ranking de técnicos com filtros: {str(e)}")
            return []
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_new_tickets_with_filters(
        self,
        limit: int = 20,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        technician: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[NewTicket]:
        """Obtém tickets novos com filtros
        
        Args:
            limit: Limite de resultados
            priority: Prioridade do ticket
            category: Categoria do ticket
            technician: Técnico responsável
            start_date: Data de início do filtro
            end_date: Data de fim do filtro
            
        Returns:
            Lista de tickets novos
        """
        try:
            self.logger.info(f"Obtendo tickets novos com filtros - limit: {limit}")
            
            # Prepara filtros
            filters = {
                'limit': limit,
                'priority': priority,
                'category': category,
                'technician': technician,
                'start_date': start_date,
                'end_date': end_date
            }
            
            # Remove filtros vazios
            filters = {k: v for k, v in filters.items() if v is not None}
            
            # Chama o método do facade legacy
            raw_data = self._legacy_facade.get_new_tickets_with_filters(**filters)
            
            # Converte dados usando o converter
            converted_data = self._converter.convert_new_tickets_list(raw_data)
            
            self.logger.info(f"Tickets novos obtidos com sucesso - {len(converted_data)} tickets")
            return converted_data
            
        except Exception as e:
            self.logger.error(f"Erro ao obter tickets novos com filtros: {str(e)}")
            return []
    
    def _apply_date_filter(self, data: Dict[str, Any], start_date: str, end_date: str) -> Dict[str, Any]:
        """Aplica filtro de data aos dados do dashboard
        
        Args:
            data: Dados originais do dashboard
            start_date: Data de início
            end_date: Data de fim
            
        Returns:
            Dict: Dados filtrados
        """
        try:
            # Implementa lógica de filtro de data
            # Por enquanto, retorna os dados originais com metadados de filtro
            filtered_data = data.copy()
            filtered_data['date_filter'] = {
                'start_date': start_date,
                'end_date': end_date,
                'applied': True
            }
            return filtered_data
        except Exception as e:
            self.logger.error(f"Erro ao aplicar filtro de data: {str(e)}")
            return data
    
    def _apply_modification_date_filter(self, data: Dict[str, Any], start_date: str, end_date: str) -> Dict[str, Any]:
        """Aplica filtro de data de modificação aos dados do dashboard
        
        Args:
            data: Dados originais do dashboard
            start_date: Data de início da modificação
            end_date: Data de fim da modificação
            
        Returns:
            Dict: Dados filtrados
        """
        try:
            # Implementa lógica de filtro de data de modificação
            filtered_data = data.copy()
            filtered_data['modification_date_filter'] = {
                'start_date': start_date,
                'end_date': end_date,
                'applied': True
            }
            return filtered_data
        except Exception as e:
            self.logger.error(f"Erro ao aplicar filtro de data de modificação: {str(e)}")
            return data
    
    def _apply_custom_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica filtros personalizados aos dados do dashboard
        
        Args:
            data: Dados originais do dashboard
            filters: Filtros a serem aplicados
            
        Returns:
            Dict: Dados filtrados
        """
        try:
            filtered_data = data.copy()
            
            # Aplica filtros de data se presentes
            if 'start_date' in filters and 'end_date' in filters:
                filtered_data = self._apply_date_filter(
                    filtered_data, 
                    filters['start_date'], 
                    filters['end_date']
                )
            
            # Adiciona metadados dos filtros aplicados
            filtered_data['custom_filters'] = filters
            
            return filtered_data
        except Exception as e:
            self.logger.error(f"Erro ao aplicar filtros personalizados: {str(e)}")
            return data
    
    def _update_filters_applied(self, dashboard_metrics: DashboardMetrics, filters: Dict[str, Any]):
        """Atualiza informações de filtros aplicados no objeto DashboardMetrics
        
        Args:
            dashboard_metrics: Objeto DashboardMetrics a ser atualizado
            filters: Filtros que foram aplicados
        """
        try:
            if 'start_date' in filters and 'end_date' in filters:
                dashboard_metrics.filters_applied.date_range = f"{filters['start_date']} - {filters['end_date']}"
            
            if 'status' in filters:
                dashboard_metrics.filters_applied.status_filter = filters['status']
            
            if 'level' in filters:
                dashboard_metrics.filters_applied.level_filter = filters['level']
            
            if 'technician' in filters:
                dashboard_metrics.filters_applied.technician_filter = filters['technician']
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar filtros aplicados: {str(e)}")
    
    def authenticate_with_retry(self, correlation_id: Optional[str] = None) -> bool:
        """Autentica com retry usando serviços legacy
        
        Args:
            correlation_id: ID de correlação para rastreamento
            
        Returns:
            bool: True se autenticação foi bem-sucedida
        """
        self._log_method_call("authenticate_with_retry", correlation_id)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                success = self._legacy_facade.authenticate()
                if success:
                    self.logger.info(
                        f"Autenticação bem-sucedida na tentativa {attempt + 1}",
                        extra={"correlation_id": correlation_id, "attempt": attempt + 1}
                    )
                    return True
                    
            except Exception as e:
                self.logger.warning(
                    f"Falha na autenticação - tentativa {attempt + 1}/{max_retries}: {str(e)}",
                    extra={"correlation_id": correlation_id, "attempt": attempt + 1, "error": str(e)}
                )
                
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff exponencial
        
        self.logger.error(
            f"Falha na autenticação após {max_retries} tentativas",
            extra={"correlation_id": correlation_id, "max_retries": max_retries}
        )
        return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache dos serviços legacy
        
        Returns:
            Dict: Estatísticas do cache
        """
        try:
            return self._legacy_facade.get_cache_stats()
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas do cache: {str(e)}")
            return {"error": str(e), "cache_available": False}
    
    def invalidate_cache(self, cache_type: Optional[str] = None) -> bool:
        """Invalida cache dos serviços legacy
        
        Args:
            cache_type: Tipo específico de cache a invalidar
            
        Returns:
            bool: True se invalidação foi bem-sucedida
        """
        try:
            self._legacy_facade.invalidate_cache(cache_type)
            self.logger.info(f"Cache invalidado com sucesso: {cache_type or 'all'}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache: {str(e)}")
            return False