# -*- coding: utf-8 -*-
"""Testes unitários para o sistema de cache unificado."""

import pytest
from datetime import datetime, timedelta
from backend.core.infrastructure.cache.unified_cache import UnifiedCache, CacheEntry


class TestUnifiedCache:
    """Testes para a classe UnifiedCache."""

    def setup_method(self):
        """Setup para cada teste."""
        self.cache = UnifiedCache()

    def test_cache_initialization(self):
        """Testa inicialização do cache."""
        assert self.cache._storage == {}
        assert self.cache._default_ttl == 300
        assert self.cache.metrics["hits"] == 0
        assert self.cache.metrics["misses"] == 0

    def test_cache_set_and_get(self):
        """Testa operações básicas de set e get."""
        # Set - UnifiedCache.set requer namespace, key_data, value
        self.cache.set("test_namespace", "test_key", "test_value")
        assert self.cache.metrics["sets"] == 1

        # Get - UnifiedCache.get requer namespace, key_data
        value = self.cache.get("test_namespace", "test_key")
        assert value == "test_value"
        assert self.cache.metrics["hits"] == 1

    def test_cache_miss(self):
        """Testa cache miss."""
        value = self.cache.get("test_namespace", "nonexistent_key")
        assert value is None
        assert self.cache.metrics["misses"] == 1

    def test_cache_ttl_expiration(self):
        """Testa expiração por TTL."""
        # Set com TTL muito baixo - parâmetro correto é ttl_seconds
        self.cache.set("test_namespace", "expire_key", "expire_value", ttl_seconds=1)
        
        # Deve estar disponível imediatamente
        assert self.cache.get("test_namespace", "expire_key") == "expire_value"
        
        # Simular expiração
        import time
        time.sleep(1.1)
        
        # Deve ter expirado
        assert self.cache.get("test_namespace", "expire_key") is None

    def test_cache_delete(self):
        """Testa remoção de itens do cache."""
        self.cache.set("test_namespace", "delete_key", "delete_value")
        assert self.cache.get("test_namespace", "delete_key") == "delete_value"
        
        # UnifiedCache usa invalidate ao invés de delete
        result = self.cache.invalidate("test_namespace", "delete_key")
        assert result == 1  # Retorna número de itens removidos
        assert self.cache.get("test_namespace", "delete_key") is None

    def test_cache_clear(self):
        """Testa limpeza completa do cache."""
        self.cache.set("test_namespace", "key1", "value1")
        self.cache.set("test_namespace", "key2", "value2")
        
        assert len(self.cache._storage) == 2
        
        # UnifiedCache usa clear_all ao invés de clear
        result = self.cache.clear_all()
        assert result == 2  # Retorna número de itens removidos
        assert len(self.cache._storage) == 0

    def test_cache_stats(self):
        """Testa estatísticas do cache."""
        # Operações para gerar estatísticas
        self.cache.set("test_namespace", "stats_key", "stats_value")
        self.cache.get("test_namespace", "stats_key")  # hit
        self.cache.get("test_namespace", "nonexistent")  # miss
        
        stats = self.cache.get_stats()
        
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert "hit_rate_percent" in stats

    def test_cache_entry_creation(self):
        """Testa criação de entrada de cache."""
        now = datetime.now()
        expires_at = now + timedelta(seconds=300)
        
        entry = CacheEntry(
            data="test_data",
            created_at=now,
            expires_at=expires_at
        )
        
        assert entry.data == "test_data"
        assert entry.created_at == now
        assert entry.expires_at == expires_at
        assert entry.access_count == 0
        assert entry.last_accessed is None

    def test_cache_with_different_data_types(self):
        """Testa cache com diferentes tipos de dados."""
        test_cases = [
            ("string_key", "string_value"),
            ("int_key", 42),
            ("list_key", [1, 2, 3]),
            ("dict_key", {"nested": "value"}),
            ("bool_key", True)
        ]
        
        for key, value in test_cases:
            self.cache.set("test_namespace", key, value)
            retrieved = self.cache.get("test_namespace", key)
            assert retrieved == value

    def test_cache_key_generation(self):
        """Testa geração de chaves de cache."""
        # _generate_key recebe namespace e key_data
        if hasattr(self.cache, '_generate_key'):
            key1 = self.cache._generate_key("namespace", "param1")
            key2 = self.cache._generate_key("namespace", "param1")
            key3 = self.cache._generate_key("namespace", "param2")
            
            assert key1 == key2  # Mesmos parâmetros = mesma chave
            assert key1 != key3  # Parâmetros diferentes = chaves diferentes
            
            # Teste com dict como key_data
            dict_key1 = self.cache._generate_key("namespace", {"a": 1, "b": 2})
            dict_key2 = self.cache._generate_key("namespace", {"b": 2, "a": 1})  # Ordem diferente
            assert dict_key1 == dict_key2  # Deve ser igual devido à normalização