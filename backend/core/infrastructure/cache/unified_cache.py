# -*- coding: utf-8 -*-
"""
Sistema de Cache Unificado

Centraliza todas as operações de cache do backend com TTL,
invalidação inteligente e observabilidade.
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """Entrada de cache com metadados."""

    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class UnifiedCache:
    """Cache unificado com TTL e observabilidade."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._storage: Dict[str, CacheEntry] = {}
        self._default_ttl = 300  # 5 minutos

        # Métricas de performance
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
            "total_size": 0,
        }

    def _generate_key(self, namespace: str, key_data: Union[str, Dict]) -> str:
        """Gera chave de cache normalizada."""
        if isinstance(key_data, dict):
            # Normalizar dicionário para string consistente
            normalized = json.dumps(key_data, sort_keys=True, default=str)
        else:
            normalized = str(key_data)

        # Criar hash para evitar chaves muito longas
        key_hash = hashlib.md5(normalized.encode()).hexdigest()
        return f"{namespace}:{key_hash}"

    def get(self, namespace: str, key_data: Union[str, Dict]) -> Optional[Any]:
        """Obtém valor do cache."""
        cache_key = self._generate_key(namespace, key_data)

        entry = self._storage.get(cache_key)
        if not entry:
            self.metrics["misses"] += 1
            self.logger.debug(f"Cache miss: {namespace}")
            return None

        # Verificar expiração
        now = datetime.now()
        if now > entry.expires_at:
            del self._storage[cache_key]
            self.metrics["evictions"] += 1
            self.metrics["misses"] += 1
            self.logger.debug(f"Cache expired: {namespace}")
            return None

        # Atualizar estatísticas de acesso
        entry.access_count += 1
        entry.last_accessed = now
        self.metrics["hits"] += 1

        self.logger.debug(f"Cache hit: {namespace} (age: {(now - entry.created_at).total_seconds():.1f}s)")
        return entry.data

    def set(
        self,
        namespace: str,
        key_data: Union[str, Dict],
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Define valor no cache."""
        cache_key = self._generate_key(namespace, key_data)
        ttl = ttl_seconds or self._default_ttl

        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl)

        entry = CacheEntry(
            data=value,
            created_at=now,
            expires_at=expires_at,
        )

        self._storage[cache_key] = entry
        self.metrics["sets"] += 1
        self.metrics["total_size"] = len(self._storage)

        self.logger.debug(f"Cache set: {namespace} (TTL: {ttl}s)")

    def invalidate(self, namespace: str, key_data: Union[str, Dict] = None) -> int:
        """Invalida cache por namespace ou chave específica."""
        if key_data is not None:
            # Invalidar chave específica
            cache_key = self._generate_key(namespace, key_data)
            if cache_key in self._storage:
                del self._storage[cache_key]
                self.metrics["evictions"] += 1
                return 1
            return 0

        # Invalidar todo o namespace
        keys_to_remove = [k for k in self._storage.keys() if k.startswith(f"{namespace}:")]
        for key in keys_to_remove:
            del self._storage[key]

        self.metrics["evictions"] += len(keys_to_remove)
        self.metrics["total_size"] = len(self._storage)

        self.logger.info(f"Invalidated {len(keys_to_remove)} entries from namespace: {namespace}")
        return len(keys_to_remove)

    def cleanup_expired(self) -> int:
        """Remove entradas expiradas."""
        now = datetime.now()
        keys_to_remove = [key for key, entry in self._storage.items() if now > entry.expires_at]

        for key in keys_to_remove:
            del self._storage[key]

        self.metrics["evictions"] += len(keys_to_remove)
        self.metrics["total_size"] = len(self._storage)

        if keys_to_remove:
            self.logger.info(f"Cleaned up {len(keys_to_remove)} expired cache entries")

        return len(keys_to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache."""
        total_requests = self.metrics["hits"] + self.metrics["misses"]
        hit_rate = (self.metrics["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.metrics,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
        }

    def clear_all(self) -> int:
        """Limpa todo o cache."""
        count = len(self._storage)
        self._storage.clear()
        self.metrics["total_size"] = 0
        self.metrics["evictions"] += count

        self.logger.info(f"Cleared all cache entries ({count} items)")
        return count


# Instância global de cache
unified_cache = UnifiedCache()
