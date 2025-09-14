"""Utilitários para monitoramento de performance e otimização de cache"""
import hashlib
import logging
import time
from functools import wraps
from typing import Any, Dict, List

from flask import request

from config.settings import active_config

logger = logging.getLogger("performance")


class PerformanceMonitor:
    """Monitor de performance para rastreamento de métricas"""

    def __init__(self):
        self.request_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0

    def record_request_time(self, duration: float):
        """Registra tempo de uma requisição"""
        try:
            if not isinstance(duration, (int, float)) or duration < 0:
                logger.warning(f"Duração inválida ignorada: {duration}")
                return

            self.request_times.append(duration)
            self.total_requests += 1

            # Mantém apenas os últimos 1000 registros
            if len(self.request_times) > 1000:
                self.request_times = self.request_times[-1000:]

        except Exception as e:
            logger.error(f"Erro ao registrar tempo de requisição: {e}")

    def record_cache_hit(self):
        """Registra um cache hit"""
        self.cache_hits += 1

    def record_cache_miss(self):
        """Registra um cache miss"""
        self.cache_misses += 1

    def get_p95_response_time(self) -> float:
        """Calcula o P95 dos tempos de resposta"""
        try:
            if not self.request_times:
                return 0.0

            sorted_times = sorted(self.request_times)
            p95_index = int(len(sorted_times) * 0.95)
            return sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]

        except Exception as e:
            logger.error(f"Erro ao calcular P95: {e}")
            return 0.0

    def get_average_response_time(self) -> float:
        """Calcula tempo médio de resposta"""
        try:
            if not self.request_times:
                return 0.0
            return sum(self.request_times) / len(self.request_times)

        except Exception as e:
            logger.error(f"Erro ao calcular tempo médio: {e}")
            return 0.0

    def get_cache_hit_rate(self) -> float:
        """Calcula taxa de cache hit"""
        try:
            total_cache_requests = self.cache_hits + self.cache_misses
            if total_cache_requests == 0:
                return 0.0
            return (self.cache_hits / total_cache_requests) * 100

        except Exception as e:
            logger.error(f"Erro ao calcular taxa de cache hit: {e}")
            return 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas completas"""
        return {
            "total_requests": self.total_requests,
            "avg_response_time": round(self.get_average_response_time() * 1000, 2),  # em ms
            "p95_response_time": round(self.get_p95_response_time() * 1000, 2),  # em ms
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.get_cache_hit_rate(), 2),
        }


# Instância global do monitor
performance_monitor = PerformanceMonitor()


def generate_cache_key(endpoint: str, **params) -> str:
    """Gera chave de cache baseada no endpoint e parâmetros"""
    try:
        if not endpoint or not isinstance(endpoint, str):
            raise ValueError("Endpoint deve ser uma string não vazia")

        # Remove parâmetros None e ordena para consistência
        clean_params = {k: v for k, v in params.items() if v is not None}
        sorted_params = sorted(clean_params.items())

        # Cria string única dos parâmetros
        params_str = "&".join([f"{k}={v}" for k, v in sorted_params])

        # Gera hash para chave compacta
        cache_key = f"{endpoint}:{hashlib.md5(params_str.encode()).hexdigest()}"

        # Validar tamanho da chave
        if len(cache_key) > 250:  # Limite do Redis
            logger.warning(f"Chave de cache muito longa: {len(cache_key)} caracteres")

        return cache_key

    except Exception as e:
        logger.error(f"Erro ao gerar chave de cache: {e}")
        # Fallback para chave simples
        return f"{endpoint}:fallback"


def monitor_performance(func):
    """Decorator para monitorar performance de funções"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            performance_monitor.record_request_time(duration)

            # Log se exceder target P95 configurado
            try:
                config_obj = active_config()
                target_p95 = config_obj.PERFORMANCE_TARGET_P95
            except:
                target_p95 = 300
            if duration * 1000 > target_p95:
                logger.warning(f"Slow request: {func.__name__} took {duration*1000:.2f}ms (target: {target_p95}ms)")

    return wrapper


def extract_filter_params() -> Dict[str, Any]:
    """Extrai parâmetros de filtro da requisição atual"""
    return {
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date"),
        "filter_type": request.args.get("filter_type", "creation"),
        "status": request.args.get("status"),
        "priority": request.args.get("priority"),
        "level": request.args.get("level"),
        "technician": request.args.get("technician"),
        "category": request.args.get("category"),
        "limit": request.args.get("limit", type=int),
        "entity_id": request.args.get("entity_id", type=int),
    }


def make_filtered_cache_key(base_key: str) -> str:
    """Cria chave de cache considerando todos os filtros da requisição"""
    filters = extract_filter_params()
    return generate_cache_key(base_key, **filters)


def cache_with_filters(timeout: int = 300):
    """Decorator para cache inteligente com suporte a filtros"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import current_app

            # Verifica se o cache está disponível
            if not hasattr(current_app, "extensions") or "cache" not in current_app.extensions:
                logger.warning("Cache não disponível, executando função diretamente")
                return func(*args, **kwargs)

            cache = current_app.extensions["cache"][list(current_app.extensions["cache"].keys())[0]]

            # Gera chave de cache baseada na função e filtros
            cache_key = make_filtered_cache_key(func.__name__)

            # Tenta buscar no cache
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    performance_monitor.record_cache_hit()
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Erro ao acessar cache: {e}")

            # Cache miss - executa função
            performance_monitor.record_cache_miss()
            logger.debug(f"Cache miss for {cache_key}")

            result = func(*args, **kwargs)

            # Armazena no cache
            try:
                cache.set(cache_key, result, timeout=timeout)
            except Exception as e:
                logger.warning(f"Erro ao armazenar no cache: {e}")

            return result

        return wrapper

    return decorator
