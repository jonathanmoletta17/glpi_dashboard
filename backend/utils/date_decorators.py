"""Decoradores para validação automática de datas em rotas da API.

Este módulo fornece decoradores que automatizam a validação de parâmetros
de data, reduzindo ainda mais a duplicação de código nas rotas.
"""

import logging
from functools import wraps
from typing import Any, Callable

from flask import jsonify, request

from utils.performance import extract_filter_params
from utils.response_formatter import ResponseFormatter
from utils.date_validator import DateValidator

logger = logging.getLogger(__name__)


def validate_date_params(support_predefined: bool = True):
    """Decorador para validação automática de parâmetros de data.

    Args:
        support_predefined: Se True, suporta ranges predefinidos via 'date_range'

    Returns:
        Decorador que valida parâmetros de data antes de executar a função
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Extrair parâmetros de filtro
                filters = extract_filter_params()

                # Normalizar e validar datas
                if support_predefined:
                    (
                        start_date,
                        end_date,
                        errors,
                    ) = DateValidator.normalize_filters_with_predefined(filters)
                else:
                    start_date, end_date, errors = DateValidator.normalize_date_filters(filters)

                # Se há erros de validação, retornar erro 400
                if errors:
                    error_messages = list(errors.values())
                    error_response = ResponseFormatter.format_error_response(
                        error_messages[0],  # Primeira mensagem como principal
                        error_messages,
                    )
                    return jsonify(error_response), 400

                # Adicionar datas normalizadas aos kwargs para a função
                kwargs["validated_start_date"] = start_date
                kwargs["validated_end_date"] = end_date
                kwargs["validated_filters"] = filters

                # Logs de observabilidade detalhados
                if start_date or end_date:
                    # Log da janela temporal aplicada
                    if start_date and end_date:
                        logger.info(
                            f"[OBSERVABILITY] Janela temporal aplicada em {func.__name__}: {start_date} até {end_date}"
                        )
                    elif start_date:
                        logger.info(
                            f"[OBSERVABILITY] Filtro de data inicial aplicado em {func.__name__}: a partir de {start_date}"
                        )
                    elif end_date:
                        logger.info(f"[OBSERVABILITY] Filtro de data final aplicado em {func.__name__}: até {end_date}")

                    # Log dos parâmetros originais recebidos
                    original_params = {k: v for k, v in filters.items() if k in ["start_date", "end_date", "date_range"]}
                    if original_params:
                        logger.info(f"[OBSERVABILITY] Parâmetros de data originais em {func.__name__}: {original_params}")
                else:
                    logger.info(f"[OBSERVABILITY] Nenhum filtro de data aplicado em {func.__name__} - usando dados completos")

                return func(*args, **kwargs)

            except Exception as e:
                logger.error(f"Erro na validação de datas para {func.__name__}: {str(e)}")
                error_response = ResponseFormatter.format_error_response(
                    "Erro interno na validação de parâmetros de data", [str(e)]
                )
                return jsonify(error_response), 500

        return wrapper

    return decorator


def require_date_range():
    """Decorador que exige que start_date e end_date sejam fornecidos.

    Returns:
        Decorador que valida que ambas as datas estão presentes
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Primeiro aplicar validação padrão
            filters = extract_filter_params()
            start_date, end_date, errors = DateValidator.normalize_date_filters(filters)

            # Verificar se ambas as datas estão presentes
            if not start_date or not end_date:
                error_response = ResponseFormatter.format_error_response(
                    "Este endpoint requer start_date e end_date",
                    ["Parâmetros start_date e end_date são obrigatórios"],
                )
                return jsonify(error_response), 400

            # Se há outros erros de validação, retornar erro 400
            if errors:
                error_messages = list(errors.values())
                error_response = ResponseFormatter.format_error_response(error_messages[0], error_messages)
                return jsonify(error_response), 400

            # Adicionar datas validadas aos kwargs
            kwargs["validated_start_date"] = start_date
            kwargs["validated_end_date"] = end_date
            kwargs["validated_filters"] = filters

            logger.debug(f"Range de datas obrigatório validado para {func.__name__}: {start_date} - {end_date}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_date_usage():
    """Decorador para log detalhado do uso de parâmetros de data.

    Returns:
        Decorador que registra informações sobre o uso de filtros de data
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            filters = extract_filter_params()

            # Log detalhado dos parâmetros recebidos
            date_params = {
                "start_date": filters.get("start_date"),
                "end_date": filters.get("end_date"),
                "date_range": filters.get("date_range"),
                "filter_type": filters.get("filter_type", "creation"),
            }

            # Filtrar apenas parâmetros não-nulos
            active_params = {k: v for k, v in date_params.items() if v is not None}

            if active_params:
                logger.info(f"Endpoint {func.__name__} chamado com parâmetros de data: {active_params}")
            else:
                logger.debug(f"Endpoint {func.__name__} chamado sem filtros de data")

            return func(*args, **kwargs)

        return wrapper

    return decorator


# Decorador composto para uso comum
def standard_date_validation(support_predefined: bool = True, log_usage: bool = True):
    """Decorador composto que aplica validação padrão e log de uso.

    Args:
        support_predefined: Se True, suporta ranges predefinidos
        log_usage: Se True, registra logs de uso dos parâmetros

    Returns:
        Decorador composto
    """

    def decorator(func: Callable) -> Callable:
        # Aplicar decoradores em ordem
        if log_usage:
            func = log_date_usage()(func)
        func = validate_date_params(support_predefined)(func)
        return func

    return decorator
