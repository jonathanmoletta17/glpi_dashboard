import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type { TechnicianRanking } from '../types/api';

export function useRanking(refreshInterval: number = 60000) {
  const [data, setData] = useState<TechnicianRanking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRanking = async () => {
    try {
      setError(null);
      const response = await apiService.getTechnicianRanking();
      setData(response);
    } catch (err) {
      setError('Erro ao carregar ranking');
      console.error('Erro em useRanking:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Buscar dados iniciais
    fetchRanking();

    // Configurar refresh automático
    const interval = setInterval(fetchRanking, refreshInterval);

    // Limpar intervalo ao desmontar
    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { data, loading, error, refetch: fetchRanking };
}