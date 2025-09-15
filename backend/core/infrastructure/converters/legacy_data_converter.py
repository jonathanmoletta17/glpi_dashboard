"""Conversor de dados legacy para modelos Pydantic.

Este módulo implementa conversões robustas entre as estruturas de dados
retornadas pelos serviços legacy e os modelos Pydantic definidos em
backend/schemas/dashboard.py.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from decimal import Decimal

from schemas.dashboard import (
    DashboardMetrics, TicketStatus, TechnicianLevel, LevelMetrics,
    NiveisMetrics, TendenciasMetrics, FiltersApplied, TechnicianRanking,
    NewTicket, ApiResponse, ApiError
)


class LegacyDataConverter:
    """Conversor para transformar dados legacy em modelos Pydantic.
    
    Esta classe centraliza toda a lógica de conversão entre os formatos
    de dados retornados pelos serviços legacy (Dict) e os modelos
    Pydantic esperados pela Clean Architecture.
    """
    
    def __init__(self):
        """Inicializa o conversor com configurações padrão."""
        self._logger = logging.getLogger(__name__)
        
    def convert_dashboard_data(self, legacy_data: Dict[str, Any]) -> DashboardMetrics:
        """Converte dados legacy completos para DashboardMetrics.
        
        Args:
            legacy_data: Dados retornados pelos serviços legacy
            
        Returns:
            DashboardMetrics: Modelo Pydantic com dados convertidos
            
        Raises:
            ValueError: Se os dados legacy estão em formato inválido
        """
        try:
            self._logger.debug("Iniciando conversão de dados legacy para DashboardMetrics")
            
            # Extrair seções principais dos dados legacy
            ticket_status = self._convert_ticket_status(
                legacy_data.get('ticket_status', {})
            )
            
            niveis_metrics = self._convert_niveis_metrics(
                legacy_data.get('niveis', {})
            )
            
            tendencias_metrics = self._convert_tendencias_metrics(
                legacy_data.get('tendencias', {})
            )
            
            technician_ranking = self._convert_technician_ranking(
                legacy_data.get('technician_ranking', [])
            )
            
            new_tickets = self._convert_new_tickets(
                legacy_data.get('new_tickets', [])
            )
            
            filters_applied = self._convert_filters_applied(
                legacy_data.get('filters', {})
            )
            
            # Construir DashboardMetrics
            dashboard_metrics = DashboardMetrics(
                novos=ticket_status.new,
                pendentes=ticket_status.assigned + ticket_status.waiting,
                progresso=ticket_status.planned,
                resolvidos=ticket_status.solved,
                total=ticket_status.total,
                niveis=niveis_metrics,
                tendencias=tendencias_metrics,
                filters_applied=filters_applied,
                timestamp=datetime.now(),
                data_source="glpi",
                is_mock_data=False
            )
            
            self._logger.info("Conversão de DashboardMetrics concluída com sucesso")
            return dashboard_metrics
            
        except Exception as e:
            self._logger.error(f"Erro na conversão de dados legacy: {e}")
            # Retorna DashboardMetrics com valores padrão em caso de erro
            default_level = LevelMetrics(
                novos=0,
                pendentes=0,
                progresso=0,
                resolvidos=0,
                total=0
            )
            return DashboardMetrics(
                novos=0,
                pendentes=0,
                progresso=0,
                resolvidos=0,
                total=0,
                niveis=NiveisMetrics(
                    n1=default_level,
                    n2=default_level,
                    n3=default_level,
                    n4=default_level
                ),
                tendencias=TendenciasMetrics(
                    novos_7d=0,
                    resolvidos_7d=0,
                    tempo_medio_resolucao=0.0
                ),
                filters_applied=FiltersApplied(
                    date_range=None,
                    status_filter=[],
                    priority_filter=[],
                    technician_filter=[],
                    category_filter=[]
                ),
                timestamp=datetime.now(),
                data_source="glpi",
                is_mock_data=False
            )
    
    def _convert_ticket_status(self, legacy_status: Dict[str, Any]) -> TicketStatus:
        """Converte dados de status de tickets legacy."""
        try:
            return TicketStatus(
                new=legacy_status.get('new', 0),
                assigned=legacy_status.get('assigned', 0),
                planned=legacy_status.get('planned', 0),
                waiting=legacy_status.get('waiting', 0),
                solved=legacy_status.get('solved', 0),
                closed=legacy_status.get('closed', 0),
                total=legacy_status.get('total', 0)
            )
        except Exception as e:
            self._logger.warning(f"Erro ao converter ticket_status: {e}")
            return TicketStatus(new=0, assigned=0, planned=0, waiting=0, solved=0, closed=0, total=0)
    
    def _convert_niveis_metrics(self, legacy_niveis: Dict[str, Any]) -> NiveisMetrics:
        """Converte métricas de níveis legacy."""
        try:
            # Converter cada nível
            n1 = self._convert_level_metrics(legacy_niveis.get('nivel1', {}))
            n2 = self._convert_level_metrics(legacy_niveis.get('nivel2', {}))
            n3 = self._convert_level_metrics(legacy_niveis.get('nivel3', {}))
            n4 = self._convert_level_metrics(legacy_niveis.get('nivel4', {}))
            
            return NiveisMetrics(
                n1=n1,
                n2=n2,
                n3=n3,
                n4=n4
            )
        except Exception as e:
            self._logger.warning(f"Erro ao converter niveis_metrics: {e}")
            return NiveisMetrics(
                n1=LevelMetrics(),
                n2=LevelMetrics(),
                n3=LevelMetrics(),
                n4=LevelMetrics()
            )
    
    def _convert_level_metrics(self, legacy_level: Dict[str, Any]) -> LevelMetrics:
        """Converte métricas de um nível específico."""
        try:
            level_name = legacy_level.get('level', 'nivel1').lower()
            
            # Mapear nome do nível para enum
            level_enum = {
                'nivel1': TechnicianLevel.N1,
                'nivel2': TechnicianLevel.N2,
                'nivel3': TechnicianLevel.N3,
                'nivel4': TechnicianLevel.N4
            }.get(level_name, TechnicianLevel.N1)
            
            return LevelMetrics(
                novos=legacy_level.get('novos', 0),
                pendentes=legacy_level.get('pendentes', 0),
                progresso=legacy_level.get('progresso', 0),
                resolvidos=legacy_level.get('resolvidos', 0),
                total=legacy_level.get('total', 0)
            )
        except Exception as e:
            self._logger.warning(f"Erro ao converter level_metrics: {e}")
            return LevelMetrics()
    
    def _convert_tendencias_metrics(self, legacy_tendencias: Dict[str, Any]) -> TendenciasMetrics:
        """Converte métricas de tendências legacy."""
        try:
            return TendenciasMetrics(
                weekly_growth=float(legacy_tendencias.get('weekly_growth', 0.0)),
                monthly_growth=float(legacy_tendencias.get('monthly_growth', 0.0)),
                resolution_trend=float(legacy_tendencias.get('resolution_trend', 0.0)),
                satisfaction_trend=float(legacy_tendencias.get('satisfaction_trend', 0.0)),
                peak_hours=legacy_tendencias.get('peak_hours', []),
                busiest_days=legacy_tendencias.get('busiest_days', [])
            )
        except Exception as e:
            self._logger.warning(f"Erro ao converter tendencias_metrics: {e}")
            return TendenciasMetrics(
                weekly_growth=0.0,
                monthly_growth=0.0,
                resolution_trend=0.0,
                satisfaction_trend=0.0,
                peak_hours=[],
                busiest_days=[]
            )
    
    def _convert_technician_ranking(self, legacy_ranking: List[Dict[str, Any]]) -> List[TechnicianRanking]:
        """Converte ranking de técnicos legacy."""
        try:
            ranking = []
            for item in legacy_ranking:
                technician = TechnicianRanking(
                    name=item.get('name', 'Desconhecido'),
                    tickets_resolved=item.get('tickets_resolved', 0),
                    avg_resolution_time=float(item.get('avg_resolution_time', 0.0)),
                    satisfaction_score=float(item.get('satisfaction_score', 0.0)),
                    level=self._convert_technician_level(item.get('level', 'nivel1'))
                )
                ranking.append(technician)
            
            return ranking
        except Exception as e:
            self._logger.warning(f"Erro ao converter technician_ranking: {e}")
            return []
    
    def _convert_technician_level(self, level_str: str) -> TechnicianLevel:
        """Converte string de nível para enum TechnicianLevel."""
        level_mapping = {
            'nivel1': TechnicianLevel.N1,
            'nivel2': TechnicianLevel.N2,
            'nivel3': TechnicianLevel.N3,
            'nivel4': TechnicianLevel.N4,
            'n1': TechnicianLevel.N1,
            'n2': TechnicianLevel.N2,
            'n3': TechnicianLevel.N3,
            'n4': TechnicianLevel.N4,
            '1': TechnicianLevel.N1,
            '2': TechnicianLevel.N2,
            '3': TechnicianLevel.N3,
            '4': TechnicianLevel.N4
        }
        
        return level_mapping.get(str(level_str).lower(), TechnicianLevel.N1)
    
    def _convert_new_tickets(self, legacy_tickets: List[Dict[str, Any]]) -> List[NewTicket]:
        """Converte lista de novos tickets legacy."""
        try:
            tickets = []
            for item in legacy_tickets:
                ticket = NewTicket(
                    id=item.get('id', 0),
                    title=item.get('title', 'Sem título'),
                    requester=item.get('requester', 'Desconhecido'),
                    priority=item.get('priority', 'normal'),
                    status=item.get('status', 'new'),
                    created_at=self._parse_datetime(item.get('created_at')),
                    category=item.get('category', 'Geral')
                )
                tickets.append(ticket)
            
            return tickets
        except Exception as e:
            self._logger.warning(f"Erro ao converter new_tickets: {e}")
            return []
    
    def _convert_filters_applied(self, legacy_filters: Dict[str, Any]) -> FiltersApplied:
        """Converte filtros aplicados legacy."""
        try:
            return FiltersApplied(
                date_range=legacy_filters.get('date_range'),
                status_filter=legacy_filters.get('status_filter', []),
                priority_filter=legacy_filters.get('priority_filter', []),
                technician_filter=legacy_filters.get('technician_filter', []),
                category_filter=legacy_filters.get('category_filter', [])
            )
        except Exception as e:
            self._logger.warning(f"Erro ao converter filters_applied: {e}")
            return FiltersApplied(
                status_filter=[],
                priority_filter=[],
                technician_filter=[],
                category_filter=[]
            )
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Converte string de data para datetime."""
        if not date_str:
            return None
        
        try:
            # Tentar diferentes formatos de data
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            self._logger.warning(f"Formato de data não reconhecido: {date_str}")
            return None
            
        except Exception as e:
            self._logger.warning(f"Erro ao converter data {date_str}: {e}")
            return None
    
    def convert_technician_ranking(self, legacy_data: List[Dict[str, Any]]) -> List[TechnicianRanking]:
        """Converte dados legacy de ranking de técnicos para modelo Pydantic.
        
        Args:
            legacy_data: Lista de dados de técnicos do serviço legacy
            
        Returns:
            List[TechnicianRanking]: Lista de rankings convertidos
        """
        try:
            self._logger.debug("Iniciating technician ranking conversion")
            
            if not isinstance(legacy_data, list):
                self._logger.warning("Dados de ranking não são uma lista, retornando lista vazia")
                return []
            
            rankings = []
            for idx, item in enumerate(legacy_data):
                try:
                    # Validar dados obrigatórios
                    if not isinstance(item, dict):
                        self._logger.warning(f"Item {idx} não é um dicionário, pulando")
                        continue
                    
                    # Extrair e validar campos
                    tech_id = self._safe_int(item.get('id', idx + 1))
                    name = self._safe_string(item.get('name', item.get('technician_name', f'Técnico {idx + 1}')))
                    tickets_resolved = self._safe_int(item.get('tickets_resolved', item.get('resolved_count', item.get('ticket_count', 0))))
                    avg_resolution_time = self._safe_float(item.get('avg_resolution_time', item.get('avg_time', 0.0)))
                    satisfaction_score = self._safe_float(item.get('satisfaction_score', item.get('rating', 0.0)))
                    level_str = item.get('level', item.get('technician_level', 'nivel1'))
                    
                    # Extrair campos de fonte de dados
                    data_source = self._safe_string(item.get('data_source', 'unknown'))
                    is_mock_data = bool(item.get('is_mock_data', False))
                    
                    # Extract data source fields
                    
                    # Calcular performance score baseado na satisfação e tempo de resolução
                    performance_score = self._safe_float(item.get('performance_score', satisfaction_score if satisfaction_score > 0 else None))
                    
                    # Criar objeto TechnicianRanking
                    ranking = TechnicianRanking(
                        id=tech_id,
                        name=name,
                        ticket_count=tickets_resolved,
                        level=self._convert_technician_level(level_str).value,
                        performance_score=performance_score,
                        data_source=data_source,
                        is_mock_data=is_mock_data
                    )
                    
                    rankings.append(ranking)
                    
                except Exception as e:
                    self._logger.warning(f"Erro ao converter item {idx} do ranking: {e}")
                    continue
            
            self._logger.info(f"Conversão de technician ranking concluída: {len(rankings)} itens")
            return rankings
            
        except Exception as e:
            self._logger.error(f"Erro na conversão de technician ranking: {e}")
            return []
    
    def convert_new_tickets(self, legacy_data: List[Dict[str, Any]]) -> List[NewTicket]:
        """Converte dados legacy de novos tickets para modelo Pydantic.
        
        Args:
            legacy_data: Lista de dados de tickets do serviço legacy
            
        Returns:
            List[NewTicket]: Lista de tickets convertidos
        """
        try:
            self._logger.debug("Iniciando conversão de new tickets")
            
            if not isinstance(legacy_data, list):
                self._logger.warning("Dados de tickets não são uma lista, retornando lista vazia")
                return []
            
            tickets = []
            for idx, item in enumerate(legacy_data):
                try:
                    # Validar dados obrigatórios
                    if not isinstance(item, dict):
                        self._logger.warning(f"Item {idx} não é um dicionário, pulando")
                        continue
                    
                    # Extrair e validar campos
                    ticket_id = str(self._safe_int(item.get('id', item.get('ticket_id', 0))))
                    title = self._safe_string(item.get('title', item.get('name', item.get('subject', f'Ticket {ticket_id}'))))
                    description = self._safe_string(item.get('description', item.get('content', title)))
                    requester = self._safe_string(item.get('requester', item.get('user', item.get('requester_name', 'Desconhecido'))))
                    priority = self._safe_string(item.get('priority', 'normal')).lower()
                    status = self._safe_string(item.get('status', 'new')).lower()
                    created_at = self._parse_datetime(item.get('created_at', item.get('date_creation', item.get('created'))))
                    
                    # Normalizar prioridade
                    priority = self._normalize_priority(priority)
                    
                    # Normalizar status
                    status = self._normalize_status(status)
                    
                    # Formatar data como string (apenas YYYY-MM-DD)
                    date_str = (created_at or datetime.now()).strftime('%Y-%m-%d')
                    
                    # Criar objeto NewTicket
                    ticket = NewTicket(
                        id=ticket_id,
                        title=title,
                        description=description,
                        date=date_str,
                        requester=requester,
                        priority=priority,
                        status=status,
                        data_source="glpi",
                        is_mock_data=False
                    )
                    
                    tickets.append(ticket)
                    
                except Exception as e:
                    self._logger.warning(f"Erro ao converter item {idx} dos tickets: {e}")
                    continue
            
            self._logger.info(f"Conversão de new tickets concluída: {len(tickets)} itens")
            return tickets
            
        except Exception as e:
            self._logger.error(f"Erro na conversão de new tickets: {e}")
            return []
    
    def convert_system_status(self, legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Converte dados legacy de status do sistema.
        
        Args:
            legacy_data: Dados de status do serviço legacy
            
        Returns:
            Dict[str, Any]: Status do sistema normalizado
        """
        try:
            self._logger.debug("Iniciando conversão de system status")
            
            if not isinstance(legacy_data, dict):
                self._logger.warning("Dados de status não são um dicionário")
                legacy_data = {}
            
            # Extrair informações básicas
            status = legacy_data.get('status', 'unknown')
            database_status = legacy_data.get('database', legacy_data.get('db_status', 'unknown'))
            api_status = legacy_data.get('api', legacy_data.get('api_status', 'unknown'))
            
            # Normalizar status
            normalized_status = {
                'status': self._normalize_health_status(status),
                'database': self._normalize_health_status(database_status),
                'api': self._normalize_health_status(api_status),
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'glpi_core': legacy_data.get('glpi_core', 'unknown'),
                    'mysql': legacy_data.get('mysql', legacy_data.get('database', 'unknown')),
                    'web_server': legacy_data.get('web_server', legacy_data.get('apache', 'unknown'))
                },
                'metrics': {
                    'response_time': self._safe_float(legacy_data.get('response_time', 0.0)),
                    'memory_usage': self._safe_float(legacy_data.get('memory_usage', 0.0)),
                    'cpu_usage': self._safe_float(legacy_data.get('cpu_usage', 0.0))
                }
            }
            
            self._logger.info("Conversão de system status concluída")
            return normalized_status
            
        except Exception as e:
            self._logger.error(f"Erro na conversão de system status: {e}")
            return {
                'status': 'error',
                'database': 'unknown',
                'api': 'unknown',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _safe_string(self, value: Any, default: str = '') -> str:
        """Converte valor para string de forma segura."""
        if value is None:
            return default
        try:
            return str(value).strip()
        except Exception:
            return default
    
    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Converte valor para int de forma segura."""
        if value is None:
            return default
        try:
            return int(float(value))  # float primeiro para lidar com decimais
        except (ValueError, TypeError):
            return default
    
    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Converte valor para float de forma segura."""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                # Remove caracteres não numéricos exceto ponto e vírgula
                value = ''.join(c for c in value if c.isdigit() or c in '.-,')
                value = value.replace(',', '.')  # Normalizar separador decimal
                if not value or value in ['-', '.', '-.']:
                    return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _normalize_priority(self, priority: str) -> str:
        """Normaliza valores de prioridade."""
        priority_mapping = {
            '1': 'very_low',
            '2': 'low', 
            '3': 'normal',
            '4': 'high',
            '5': 'very_high',
            'muito_baixa': 'very_low',
            'baixa': 'low',
            'normal': 'normal',
            'alta': 'high',
            'muito_alta': 'very_high',
            'critical': 'very_high',
            'critica': 'very_high'
        }
        
        normalized = priority.lower().strip()
        return priority_mapping.get(normalized, 'normal')
    
    def _normalize_status(self, status: str) -> str:
        """Normaliza valores de status."""
        status_mapping = {
            '1': 'new',
            '2': 'assigned',
            '3': 'planned',
            '4': 'waiting',
            '5': 'solved',
            '6': 'closed',
            'novo': 'new',
            'atribuido': 'assigned',
            'planejado': 'planned',
            'aguardando': 'waiting',
            'resolvido': 'solved',
            'fechado': 'closed',
            'open': 'new',
            'in_progress': 'assigned'
        }
        
        normalized = status.lower().strip()
        return status_mapping.get(normalized, 'new')
    
    def _normalize_health_status(self, status: str) -> str:
        """Normaliza valores de status de saúde."""
        if not status:
            return 'unknown'
        
        status = str(status).lower().strip()
        
        if status in ['ok', 'healthy', 'up', 'connected', 'active', '1', 'true']:
            return 'healthy'
        elif status in ['error', 'down', 'disconnected', 'inactive', '0', 'false', 'failed']:
            return 'unhealthy'
        elif status in ['warning', 'degraded', 'slow']:
            return 'degraded'
        else:
            return 'unknown'
    
    def validate_converted_data(self, dashboard_metrics: DashboardMetrics) -> bool:
        """Valida se os dados convertidos estão consistentes.
        
        Args:
            dashboard_metrics: Dados convertidos para validar
            
        Returns:
            True se os dados são válidos, False caso contrário
        """
        try:
            # Validações básicas
            if dashboard_metrics.total < 0:
                self._logger.error("Total de tickets não pode ser negativo")
                return False
            
            # Validar consistência de status de tickets
            status_sum = (
                dashboard_metrics.novos +
                dashboard_metrics.pendentes +
                dashboard_metrics.progresso +
                dashboard_metrics.resolvidos
            )
            
            if status_sum != dashboard_metrics.total:
                self._logger.warning(
                    f"Inconsistência nos status: soma={status_sum}, total={dashboard_metrics.total}"
                )
            
            # Validar se os níveis existem
            if not dashboard_metrics.niveis:
                self._logger.warning("Dados de níveis não encontrados")
                return False
            
            self._logger.info("Validação de dados convertidos concluída com sucesso")
            return True
            
        except Exception as e:
            self._logger.error(f"Erro na validação de dados convertidos: {e}")
            return False
    
    def convert_new_tickets_list(self, legacy_data: Dict[str, Any]) -> List[NewTicket]:
        """Converte dados legacy de tickets para lista de NewTicket.
        
        Args:
            legacy_data: Dados legacy contendo tickets
            
        Returns:
            List[NewTicket]: Lista de tickets convertidos
        """
        try:
            self._logger.debug("Iniciando conversão de lista de tickets")
            
            if not isinstance(legacy_data, dict):
                self._logger.warning("Dados de entrada não são um dicionário")
                return []
            
            # Extrair dados dos tickets
            tickets_data = legacy_data.get('data', [])
            if not isinstance(tickets_data, list):
                self._logger.warning("Dados de tickets não são uma lista")
                return []
            
            converted_tickets = []
            
            for ticket_data in tickets_data:
                try:
                    # Usar o método existente convert_new_tickets para cada ticket
                    ticket_list = self.convert_new_tickets({'data': [ticket_data]})
                    if ticket_list:
                        converted_tickets.extend(ticket_list)
                except Exception as e:
                    self._logger.warning(f"Erro ao converter ticket individual: {e}")
                    continue
            
            self._logger.info(f"Conversão de lista de tickets concluída: {len(converted_tickets)} tickets")
            return converted_tickets
            
        except Exception as e:
            self._logger.error(f"Erro na conversão de lista de tickets: {e}")
            return []
    
    def convert_technician_ranking_list(self, legacy_data: Dict[str, Any]) -> List[TechnicianRanking]:
        """Converte dados legacy de ranking de técnicos para lista de TechnicianRanking.
        
        Args:
            legacy_data: Dados legacy contendo ranking de técnicos
            
        Returns:
            List[TechnicianRanking]: Lista de rankings convertidos
        """
        try:
            self._logger.debug("Iniciando conversão de lista de ranking de técnicos")
            
            # Se recebemos uma lista diretamente (do GLPIServiceFacade)
            if isinstance(legacy_data, list):
                self._logger.debug("Dados recebidos como lista direta")
                return self.convert_technician_ranking(legacy_data)
            
            # Se recebemos um dicionário
            if not isinstance(legacy_data, dict):
                self._logger.warning("Dados de entrada não são um dicionário nem lista")
                return []
            
            # Extrair dados dos técnicos
            technicians_data = legacy_data.get('data', [])
            if not isinstance(technicians_data, list):
                self._logger.warning("Dados de técnicos não são uma lista")
                return []
            
            # Usar o método existente convert_technician_ranking
            converted_rankings = self.convert_technician_ranking(technicians_data)
            
            self._logger.info(f"Conversão de lista de ranking de técnicos concluída: {len(converted_rankings)} técnicos")
            return converted_rankings
            
        except Exception as e:
            self._logger.error(f"Erro na conversão de lista de ranking de técnicos: {e}")
            return []