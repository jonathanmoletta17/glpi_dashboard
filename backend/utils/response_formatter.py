import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("response_formatter")


class ResponseFormatter:
    """Utilitário para formatação unificada das respostas da API"""

    @staticmethod
    def format_dashboard_response(
        raw_metrics: Dict,
        filters: Optional[Dict] = None,
        start_time: Optional[float] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Formata resposta das métricas do dashboard de forma unificada"""
        try:
            # Garantir que raw_metrics seja um dict
            raw_metrics = raw_metrics or {}

            # Calcular tempo de execução se fornecido
            execution_time = None
            if start_time and isinstance(start_time, (int, float)):
                execution_time = round((time.time() - start_time) * 1000, 2)

            # Processar dados dos níveis
            niveis_data = {}

            # Se há estrutura by_level (com filtros)
            if raw_metrics and "by_level" in raw_metrics and isinstance(raw_metrics["by_level"], dict):
                for level_name, level_data in raw_metrics["by_level"].items():
                    if not isinstance(level_data, dict):
                        logger.warning(f"Dados do nível {level_name} inválidos: {type(level_data)}")
                        continue

                    level_key = str(level_name).lower()
                    niveis_data[level_key] = {
                        "novos": max(0, int(level_data.get("Novo", 0) or 0)),
                        "pendentes": max(0, int(level_data.get("Pendente", 0) or 0)),
                        "progresso": max(
                            0,
                            (
                                int(level_data.get("Processando (atribuído)", 0) or 0)
                                + int(level_data.get("Processando (planejado)", 0) or 0)
                            ),
                        ),
                        "resolvidos": max(
                            0,
                            (int(level_data.get("Solucionado", 0) or 0) + int(level_data.get("Fechado", 0) or 0)),
                        ),
                    }

            # Se há estrutura niveis (sem filtros)
            elif raw_metrics and "niveis" in raw_metrics and isinstance(raw_metrics["niveis"], dict):
                for level_name, level_data in raw_metrics["niveis"].items():
                    if not isinstance(level_data, dict):
                        logger.warning(f"Dados do nível {level_name} inválidos: {type(level_data)}")
                        continue

                    # Validar e sanitizar dados do nível
                    sanitized_data = {}
                    for key in [
                        "novos",
                        "pendentes",
                        "progresso",
                        "resolvidos",
                        "total",
                    ]:
                        value = level_data.get(key, 0)
                        sanitized_data[key] = max(0, int(value or 0))

                    niveis_data[str(level_name)] = sanitized_data

            # Garantir que todos os níveis existam
            for level in ["n1", "n2", "n3", "n4"]:
                if level not in niveis_data:
                    niveis_data[level] = {
                        "novos": 0,
                        "pendentes": 0,
                        "progresso": 0,
                        "resolvidos": 0,
                        "total": 0,
                    }
                else:
                    # Calcular total para cada nível
                    level_data = niveis_data[level]
                    level_data["total"] = (
                        level_data.get("novos", 0)
                        + level_data.get("pendentes", 0)
                        + level_data.get("progresso", 0)
                        + level_data.get("resolvidos", 0)
                    )

            # Extrair totais gerais
            if raw_metrics and "general" in raw_metrics and isinstance(raw_metrics["general"], dict):
                # Com filtros - usar dados gerais
                general = raw_metrics["general"]
                novos = max(0, int(general.get("Novo", 0) or 0))
                pendentes = max(0, int(general.get("Pendente", 0) or 0))
                progresso = max(
                    0,
                    (
                        int(general.get("Processando (atribuído)", 0) or 0)
                        + int(general.get("Processando (planejado)", 0) or 0)
                    ),
                )
                resolvidos = max(
                    0,
                    (int(general.get("Solucionado", 0) or 0) + int(general.get("Fechado", 0) or 0)),
                )
            else:
                # Sem filtros - calcular dos níveis
                try:
                    novos = sum(level.get("novos", 0) for level in niveis_data.values() if isinstance(level, dict))
                    pendentes = sum(level.get("pendentes", 0) for level in niveis_data.values() if isinstance(level, dict))
                    progresso = sum(level.get("progresso", 0) for level in niveis_data.values() if isinstance(level, dict))
                    resolvidos = sum(level.get("resolvidos", 0) for level in niveis_data.values() if isinstance(level, dict))
                except Exception as e:
                    logger.error(f"Erro ao calcular totais dos níveis: {e}")
                    novos = pendentes = progresso = resolvidos = 0

            total = novos + pendentes + progresso + resolvidos

            # Adicionar totais gerais aos níveis
            niveis_data["geral"] = {
                "novos": novos,
                "pendentes": pendentes,
                "progresso": progresso,
                "resolvidos": resolvidos,
                "total": total,
            }

            # Criar resposta seguindo o schema DashboardMetrics
            response = {
                "success": True,
                "data": {
                    # Campos diretos do schema DashboardMetrics
                    "novos": novos,
                    "pendentes": pendentes,
                    "progresso": progresso,
                    "resolvidos": resolvidos,
                    "total": total,
                    "niveis": niveis_data,
                    "tendencias": {
                        "novos_hoje": 0,
                        "resolvidos_hoje": 0,
                        "pendencias_ontem": 0,
                        "variacao_pendentes": 0,
                    },
                    "filters_applied": filters or {},
                    "timestamp": datetime.now().isoformat(),
                },
            }

            if execution_time is not None:
                response["tempo_execucao"] = execution_time

            if correlation_id:
                response["correlation_id"] = correlation_id

            return response

        except Exception as e:
            logger.error(f"Erro ao formatar resposta do dashboard: {e}")
            return ResponseFormatter.format_error_response(message="Erro ao formatar métricas do dashboard", errors=[str(e)])

    @staticmethod
    def format_error_response(
        message: str,
        errors: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Formata resposta de erro de forma unificada"""
        try:
            # Garantir que message seja string
            message = str(message) if message else "Erro desconhecido"

            if errors and not isinstance(errors, list):
                errors = [str(errors)]

            response: Dict[str, Any] = {
                "success": False,
                "message": message,
                "errors": errors or [],
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            if correlation_id:
                response["correlation_id"] = correlation_id
            return response
        except Exception as e:
            # Fallback em caso de erro na formatação
            fallback_response: Dict[str, Any] = {
                "success": False,
                "message": "Erro interno na formatação de resposta",
                "errors": [str(e)],
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            if correlation_id:
                fallback_response["correlation_id"] = correlation_id
            return fallback_response

    @staticmethod
    def format_success_response(
        data: Any,
        message: str = "Operação realizada com sucesso",
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Formata resposta de sucesso de forma unificada"""
        try:
            # Garantir que message seja string
            message = str(message) if message else "Operação realizada com sucesso"

            response: Dict[str, Any] = {
                "success": True,
                "data": data,
                "message": message,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            if correlation_id:
                response["correlation_id"] = correlation_id
            return response
        except Exception as e:
            logger.error(f"Erro ao formatar resposta de sucesso: {e}")
            # Fallback em caso de erro na formatação
            fallback_response: Dict[str, Any] = {
                "success": True,
                "data": None,
                "message": "Erro na formatação da resposta",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            if correlation_id:
                fallback_response["correlation_id"] = correlation_id
            return fallback_response

    @staticmethod
    def success(data: Any, message: str = "Operação realizada com sucesso") -> Dict[str, Any]:
        """Método de conveniência para resposta de sucesso"""
        return ResponseFormatter.format_success_response(data, message)

    @staticmethod
    def error(message: str, errors: Optional[List] = None) -> Dict[str, Any]:
        """Método de conveniência para resposta de erro"""
        return ResponseFormatter.format_error_response(message, errors)
