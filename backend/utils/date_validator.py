"""Utilitário centralizado para validação e normalização de datas.

Este módulo fornece funções para validar e normalizar parâmetros de data
usados em toda a aplicação, eliminando duplicação de código.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class DateValidationError(Exception):
    """Exceção customizada para erros de validação de data."""

    pass


class DateValidator:
    """Classe para validação e normalização de datas."""

    DATE_FORMAT = "%Y-%m-%d"

    @classmethod
    def validate_date_format(cls, date_str: str) -> bool:
        """Valida se a string de data está no formato YYYY-MM-DD.

        Args:
            date_str: String da data para validar

        Returns:
            bool: True se válida, False caso contrário
        """
        if not date_str:
            return False

        try:
            datetime.strptime(date_str, cls.DATE_FORMAT)
            return True
        except (ValueError, TypeError):
            return False

    @classmethod
    def validate_date_range(cls, start_date: Optional[str], end_date: Optional[str]) -> bool:
        """Valida se o range de datas é válido (start_date <= end_date).

        Args:
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)

        Returns:
            bool: True se válido, False caso contrário
        """
        if not start_date or not end_date:
            return True  # Range parcial é válido

        if not cls.validate_date_format(start_date) or not cls.validate_date_format(end_date):
            return False

        try:
            start_dt = datetime.strptime(start_date, cls.DATE_FORMAT)
            end_dt = datetime.strptime(end_date, cls.DATE_FORMAT)
            return start_dt <= end_dt
        except (ValueError, TypeError):
            return False

    @classmethod
    def normalize_date_filters(cls, filters: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Dict[str, str]]:
        """Normaliza e valida filtros de data de um dicionário de parâmetros.

        Args:
            filters: Dicionário com parâmetros que podem incluir start_date e end_date

        Returns:
            Tuple contendo:
            - start_date normalizada (ou None)
            - end_date normalizada (ou None)
            - dict com erros de validação (vazio se tudo válido)

        Raises:
            DateValidationError: Se houver erro de validação
        """
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        errors = {}

        # Validar formato da data de início
        if start_date and not cls.validate_date_format(start_date):
            errors["start_date"] = "Formato de start_date inválido. Use YYYY-MM-DD"

        # Validar formato da data de fim
        if end_date and not cls.validate_date_format(end_date):
            errors["end_date"] = "Formato de end_date inválido. Use YYYY-MM-DD"

        # Se há erros de formato, retornar imediatamente
        if errors:
            return start_date, end_date, errors

        # Validar range de datas
        if not cls.validate_date_range(start_date, end_date):
            errors["date_range"] = "Data de início não pode ser posterior à data de fim"

        return start_date, end_date, errors

    @classmethod
    def get_predefined_ranges(cls) -> Dict[str, Dict[str, str]]:
        """Retorna ranges de data predefinidos comumente usados.

        Returns:
            Dict com ranges predefinidos (hoje, última semana, último mês, etc.)
        """
        today = datetime.now()

        return {
            "today": {
                "start_date": today.strftime(cls.DATE_FORMAT),
                "end_date": today.strftime(cls.DATE_FORMAT),
            },
            "yesterday": {
                "start_date": (today - timedelta(days=1)).strftime(cls.DATE_FORMAT),
                "end_date": (today - timedelta(days=1)).strftime(cls.DATE_FORMAT),
            },
            "last_7_days": {
                "start_date": (today - timedelta(days=7)).strftime(cls.DATE_FORMAT),
                "end_date": today.strftime(cls.DATE_FORMAT),
            },
            "last_30_days": {
                "start_date": (today - timedelta(days=30)).strftime(cls.DATE_FORMAT),
                "end_date": today.strftime(cls.DATE_FORMAT),
            },
            "last_90_days": {
                "start_date": (today - timedelta(days=90)).strftime(cls.DATE_FORMAT),
                "end_date": today.strftime(cls.DATE_FORMAT),
            },
            "current_month": {
                "start_date": today.replace(day=1).strftime(cls.DATE_FORMAT),
                "end_date": today.strftime(cls.DATE_FORMAT),
            },
            "last_month": {
                "start_date": (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime(cls.DATE_FORMAT),
                "end_date": (today.replace(day=1) - timedelta(days=1)).strftime(cls.DATE_FORMAT),
            },
        }

    @classmethod
    def expand_predefined_range(cls, range_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Expande um nome de range predefinido para start_date e end_date.

        Args:
            range_name: Nome do range predefinido

        Returns:
            Tuple com (start_date, end_date) ou (None, None) se range inválido
        """
        predefined_ranges = cls.get_predefined_ranges()

        if range_name not in predefined_ranges:
            logger.warning(f"Range predefinido '{range_name}' não encontrado")
            return None, None

        range_data = predefined_ranges[range_name]
        return range_data["start_date"], range_data["end_date"]

    @classmethod
    def construir_criterios_filtro_data(
        cls, start_date: Optional[str], end_date: Optional[str], field_id: str = "15", criteria_start_index: int = 0
    ) -> Dict[str, str]:
        """Constrói critérios de filtro de data para a API GLPI de forma centralizada.

        Esta função implementa os "3 Pilares para Criar Qualquer Métrica no GLPI":
        - O Quê: itemtype (Ticket)
        - Quando: filtro de data (campo 15 - data de criação)
        - Como Agrupar: por critério específico (técnico, categoria, etc.)

        Args:
            start_date: Data de início no formato YYYY-MM-DD (opcional)
            end_date: Data de fim no formato YYYY-MM-DD (opcional)
            field_id: ID do campo de data na API GLPI (padrão: "15" para data de criação)
            criteria_start_index: Índice inicial para os critérios (padrão: 0)

        Returns:
            Dict com critérios formatados para a API GLPI

        Raises:
            DateValidationError: Se as datas forem inválidas

        Example:
            >>> criterios = DateValidator.construir_criterios_filtro_data(
            ...     "2024-01-01", "2024-01-31", "15", 0
            ... )
            >>> print(criterios)
            {
                "criteria[0][field]": "15",
                "criteria[0][searchtype]": "morethan",
                "criteria[0][value]": "2024-01-01 00:00:00",
                "criteria[1][link]": "AND",
                "criteria[1][field]": "15",
                "criteria[1][searchtype]": "lessthan",
                "criteria[1][value]": "2024-01-31 23:59:59"
            }
        """
        criterios = {}

        # Validar datas se fornecidas
        if start_date and not cls.validate_date_format(start_date):
            raise DateValidationError(f"Formato de start_date inválido: {start_date}. Use YYYY-MM-DD")

        if end_date and not cls.validate_date_format(end_date):
            raise DateValidationError(f"Formato de end_date inválido: {end_date}. Use YYYY-MM-DD")

        if start_date and end_date and not cls.validate_date_range(start_date, end_date):
            raise DateValidationError(f"Range de datas inválido: {start_date} > {end_date}")

        current_index = criteria_start_index

        # Adicionar critério de data de início (maior que)
        if start_date:
            start_datetime = f"{start_date} 00:00:00"
            criterios.update(
                {
                    f"criteria[{current_index}][field]": field_id,
                    f"criteria[{current_index}][searchtype]": "morethan",
                    f"criteria[{current_index}][value]": start_datetime,
                }
            )
            current_index += 1

        # Adicionar critério de data de fim (menor que)
        if end_date:
            end_datetime = f"{end_date} 23:59:59"

            # Se já temos critério de início, adicionar link AND
            if start_date:
                criterios[f"criteria[{current_index}][link]"] = "AND"

            criterios.update(
                {
                    f"criteria[{current_index}][field]": field_id,
                    f"criteria[{current_index}][searchtype]": "lessthan",
                    f"criteria[{current_index}][value]": end_datetime,
                }
            )
            current_index += 1

        logger.debug(
            f"[FILTER_BUILDER] Critérios construídos: start_date={start_date}, "
            f"end_date={end_date}, field_id={field_id}, total_criterios={len(criterios)//3 if criterios else 0}"
        )

        return criterios

    @classmethod
    def normalize_filters_with_predefined(cls, filters: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Dict[str, str]]:
        """Normaliza filtros suportando ranges predefinidos e datas customizadas.

        Args:
            filters: Dicionário que pode conter 'date_range' (predefinido) ou 'start_date'/'end_date'

        Returns:
            Tuple contendo:
            - start_date normalizada (ou None)
            - end_date normalizada (ou None)
            - dict com erros de validação (vazio se tudo válido)
        """
        # Verificar se há um range predefinido
        date_range = filters.get("date_range")
        if date_range:
            start_date, end_date = cls.expand_predefined_range(date_range)
            if start_date is None:
                logger.warning(f"[OBSERVABILITY] Range predefinido inválido: '{date_range}'")
                return (
                    None,
                    None,
                    {"date_range": f"Range predefinido '{date_range}' inválido"},
                )

            # Atualizar filters com as datas expandidas para log
            filters["start_date"] = start_date
            filters["end_date"] = end_date

            logger.info(f"[OBSERVABILITY] Range predefinido '{date_range}' expandido para janela: {start_date} até {end_date}")

            # Log adicional sobre o tipo de range
            from datetime import datetime

            if start_date and end_date:
                start_dt = datetime.strptime(start_date, cls.DATE_FORMAT)
                end_dt = datetime.strptime(end_date, cls.DATE_FORMAT)
                days_diff = (end_dt - start_dt).days + 1
                logger.info(f"[OBSERVABILITY] Janela temporal: {days_diff} dia(s) de dados")

        # Usar normalização padrão
        return cls.normalize_date_filters(filters)


# Funções de conveniência para compatibilidade
def validate_date_format(date_str: str) -> bool:
    """Função de conveniência para validar formato de data."""
    return DateValidator.validate_date_format(date_str)


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> bool:
    """Função de conveniência para validar range de datas."""
    return DateValidator.validate_date_range(start_date, end_date)


def normalize_date_filters(filters: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Dict[str, str]]:
    """Função de conveniência para normalizar filtros de data."""
    return DateValidator.normalize_date_filters(filters)


def normalize_filters_with_predefined(filters: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Dict[str, str]]:
    """Função de conveniência para normalizar filtros com suporte a ranges predefinidos."""
    return DateValidator.normalize_filters_with_predefined(filters)
