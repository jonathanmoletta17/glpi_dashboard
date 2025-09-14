import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type { DashboardMetrics } from '../types/api';

export function useMetrics(refreshInterval: number = 30000) {
  const [data, setData] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    try {
      setError(null);
      const response = await apiService.getMetrics();
      setData(response);
    } catch (err) {
      setError('Erro ao carregar métricas');
      console.error('Erro em useMetrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Buscar dados iniciais
    fetchMetrics();

    // Configurar refresh automático
    const interval = setInterval(fetchMetrics, refreshInterval);

    // Limpar intervalo ao desmontar
    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { data, loading, error, refetch: fetchMetrics };
}