"""Builder declarativo para `criteria` da API GLPI.

O GLPI utiliza filtros em formato JSON para paginação e consultas complexas. O
objetivo desta abstração é evitar `string templates` dispersos e tornar o
versionamento dos filtros previsível, atendendo ao Doc 03.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Literal, Sequence

SearchType = Literal['contains', 'equals', 'notequals', 'greaterthan', 'lessthan', 'morethan', 'lessthan_or_equal', 'startswith']
LogicalOperator = Literal['AND', 'OR']
SortOrder = Literal['ASC', 'DESC']


@dataclass(frozen=True)
class Filter:
    """Filtro individual conforme o contrato do GLPI."""

    field: str
    value: Any
    searchtype: SearchType = 'equals'
    logical: LogicalOperator = 'AND'


@dataclass(frozen=True)
class Sort:
    field: str
    order: SortOrder = 'ASC'


@dataclass(frozen=True)
class Limit:
    max: int = 50
    offset: int = 0


@dataclass(frozen=True)
class CriteriaSpec:
    """Especificação completa de um criteria."""

    filters: Sequence[Filter] = field(default_factory=list)
    sort: Sequence[Sort] = field(default_factory=list)
    limit: Limit = field(default_factory=Limit)


class CriteriaBuilder:
    """Builder simples e imutável de criteria."""

    def __init__(self, spec: CriteriaSpec | None = None):
        self._filters: List[Filter] = list(spec.filters) if spec else []
        self._sort: List[Sort] = list(spec.sort) if spec else []
        self._limit: Limit = spec.limit if spec else Limit()

    def and_filter(self, *, field: str, value: Any, searchtype: SearchType = 'equals') -> 'CriteriaBuilder':
        next_builder = CriteriaBuilder(CriteriaSpec(self._filters, self._sort, self._limit))
        next_builder._filters.append(Filter(field=field, value=value, searchtype=searchtype, logical='AND'))
        return next_builder

    def or_filter(self, *, field: str, value: Any, searchtype: SearchType = 'equals') -> 'CriteriaBuilder':
        next_builder = CriteriaBuilder(CriteriaSpec(self._filters, self._sort, self._limit))
        next_builder._filters.append(Filter(field=field, value=value, searchtype=searchtype, logical='OR'))
        return next_builder

    def sort_by(self, field: str, order: SortOrder = 'ASC') -> 'CriteriaBuilder':
        next_builder = CriteriaBuilder(CriteriaSpec(self._filters, self._sort, self._limit))
        next_builder._sort.append(Sort(field=field, order=order))
        return next_builder

    def with_limit(self, *, max_items: int, offset: int = 0) -> 'CriteriaBuilder':
        next_builder = CriteriaBuilder(CriteriaSpec(self._filters, self._sort, self._limit))
        next_builder._limit = Limit(max=max_items, offset=offset)
        return next_builder

    def build(self) -> str:
        """Retorna a string JSON final validada."""

        payload = {
            'criteria': [
                {
                    'field': f.field,
                    'searchtype': f.searchtype,
                    'value': f.value,
                    'link': f.logical,
                }
                for f in self._filters
            ],
            'sort': [
                {
                    'field': s.field,
                    'order': s.order,
                }
                for s in self._sort
            ],
            'range': [self._limit.offset, self._limit.offset + self._limit.max],
        }
        return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))

    def as_dict(self) -> dict[str, Any]:
        """Versão em dicionário usada em testes e mocks."""

        return json.loads(self.build())


# Templates reutilizados pelos workers -------------------------------

def default_tickets_criteria(*, updated_after: str | None = None) -> CriteriaBuilder:
    """Cria criteria padrão para tickets ativos."""

    builder = CriteriaBuilder().and_filter(field='is_deleted', value=0, searchtype='equals')
    builder = builder.and_filter(field='status', value='notclosed', searchtype='equals')
    if updated_after:
        builder = builder.and_filter(field='date_mod', value=updated_after, searchtype='morethan')
    return builder.sort_by('date_mod', order='DESC').with_limit(max_items=100)


def technician_users_criteria() -> CriteriaBuilder:
    """Criteria de técnicos ativos usados no ranking."""

    return (
        CriteriaBuilder()
        .and_filter(field='is_active', value=1)
        .and_filter(field='is_deleted', value=0)
        .sort_by('name', order='ASC')
        .with_limit(max_items=200)
    )
