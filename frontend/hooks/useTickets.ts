import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type { NewTicket } from '../types/api';

export function useTickets(limit: number = 8, refreshInterval: number = 30000) {
  const [data, setData] = useState<NewTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTickets = async () => {
    try {
      setError(null);
      const response = await apiService.getNewTickets(limit);
      setData(response);
    } catch (err) {
      setError('Erro ao carregar tickets');
      console.error('Erro em useTickets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Buscar dados iniciais
    fetchTickets();

    // Configurar refresh automático
    const interval = setInterval(fetchTickets, refreshInterval);

    // Limpar intervalo ao desmontar
    return () => clearInterval(interval);
  }, [limit, refreshInterval]);

  return { data, loading, error, refetch: fetchTickets };
}