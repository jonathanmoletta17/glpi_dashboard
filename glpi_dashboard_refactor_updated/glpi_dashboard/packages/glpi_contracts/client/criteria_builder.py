"""Criteria builder for GLPI API queries.

The GLPI API uses a JSON "criteria" parameter to filter, sort and limit
results. This module provides a declarative builder to compose criteria
objects safely. This is a simplified placeholder; extend with full support
for the GLPI criteria syntax as needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union, Dict, Any


class FilterOperator(str, Enum):
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    IN = "IN"


@dataclass(frozen=True)
class Filter:
    field: str
    operator: FilterOperator
    value: Union[str, int, float, List[Union[str, int, float]]]


@dataclass(frozen=True)
class Sort:
    field: str
    ascending: bool = True


@dataclass
class CriteriaSpec:
    filters: List[Filter] = field(default_factory=list)
    sort: Optional[Sort] = None
    limit: Optional[int] = None

    def add_filter(self, field: str, operator: FilterOperator, value: Union[str, int, float, List[Union[str, int, float]]]) -> "CriteriaSpec":
        self.filters.append(Filter(field=field, operator=operator, value=value))
        return self

    def set_sort(self, field: str, ascending: bool = True) -> "CriteriaSpec":
        self.sort = Sort(field=field, ascending=ascending)
        return self

    def set_limit(self, limit: int) -> "CriteriaSpec":
        self.limit = limit
        return self

    def to_json(self) -> str:
        """Serialize criteria spec to a JSON string according to GLPI format."""
        import json
        criteria: Dict[str, Any] = {}
        if self.filters:
            criteria["criteria"] = [
                {
                    "field": f.field,
                    "searchtype": f.operator.value,
                    "value": f.value,
                }
                for f in self.filters
            ]
        if self.sort:
            criteria["sort"] = [self.sort.field]
            criteria["order"] = ["ASC" if self.sort.ascending else "DESC"]
        if self.limit is not None:
            criteria["limit"] = self.limit
        return json.dumps(criteria)