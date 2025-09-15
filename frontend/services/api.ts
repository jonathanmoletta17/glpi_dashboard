import httpClientWithRetry from './httpClient';
import type { 
  DashboardMetrics, 
  TechnicianRanking, 
  NewTicket, 
  SystemStatus,
  ApiResponse 
} from '../types/api';

export const apiService = {
  async getMetrics(): Promise<DashboardMetrics> {
    try {
      const response = await httpClientWithRetry.get<any>('/metrics');
      
      // A API retorna uma estrutura aninhada: response.data.data.data
      // Onde o primeiro 'data' é do axios, o segundo é do wrapper da API, e o terceiro são os dados reais
      if (response.data?.data?.data) {
        const metrics = response.data.data.data;
        
        // Verificar se tem a estrutura de níveis esperada
        if (metrics.niveis) {
          // Criar estrutura compatível com DashboardMetrics
          return {
            niveis: {
              n1: metrics.niveis.n1 || { novos: 0, pendentes: 0, progresso: 0, resolvidos: 0, total: 0 },
              n2: metrics.niveis.n2 || { novos: 0, pendentes: 0, progresso: 0, resolvidos: 0, total: 0 },
              n3: metrics.niveis.n3 || { novos: 0, pendentes: 0, progresso: 0, resolvidos: 0, total: 0 },
              n4: metrics.niveis.n4 || { novos: 0, pendentes: 0, progresso: 0, resolvidos: 0, total: 0 },
              geral: {
                novos: metrics.novos || 0,
                pendentes: metrics.pendentes || 0,
                progresso: metrics.progresso || 0,
                resolvidos: metrics.resolvidos || 0,
                total: metrics.total || 0
              }
            },
            tendencias: metrics.tendencias || {
              novos: '0%',
              pendentes: '0%',
              progresso: '0%',
              resolvidos: '0%'
            },
            data_source: metrics.data_source || 'glpi',
            is_mock_data: metrics.is_mock_data ?? false,
            timestamp: metrics.timestamp
          };
        }
      }
      
      // Fallback para estrutura padrão se não houver dados
      console.warn('Estrutura de dados inesperada na resposta da API:', response.data);
      return createDefaultMetrics();
    } catch (error) {
      console.error('Erro ao buscar métricas:', error);
      // Retornar dados padrão em caso de erro
      return createDefaultMetrics();
    }
  },

  async getTechnicianRanking(): Promise<TechnicianRanking[]> {
    try {
      const response = await httpClientWithRetry.get<ApiResponse<TechnicianRanking[]>>('/technicians/ranking');
      
      if (response.data?.data) {
        return response.data.data;
      } else if (Array.isArray(response.data)) {
        return response.data;
      }
      
      return [];
    } catch (error) {
      console.error('Erro ao buscar ranking:', error);
      return [];
    }
  },

  async getNewTickets(limit: number = 8): Promise<NewTicket[]> {
    try {
      const response = await httpClientWithRetry.get<ApiResponse<NewTicket[]>>('/tickets/new', {
        params: { limit }
      });
      
      if (response.data?.data) {
        return response.data.data;
      } else if (Array.isArray(response.data)) {
        return response.data;
      }
      
      return [];
    } catch (error) {
      console.error('Erro ao buscar tickets:', error);
      return [];
    }
  },

  async getSystemStatus(): Promise<SystemStatus> {
    try {
      const response = await httpClientWithRetry.get<ApiResponse<SystemStatus>>('/status');
      
      if (response.data?.data) {
        return response.data.data;
      } else if (response.data && 'api' in response.data) {
        return response.data as unknown as SystemStatus;
      }
      
      return {
        api: 'offline',
        glpi: 'offline',
        glpi_message: 'Não foi possível conectar ao sistema',
        glpi_response_time: 0,
        last_update: new Date().toISOString(),
        version: '1.0.0'
      };
    } catch (error) {
      console.error('Erro ao buscar status:', error);
      return {
        api: 'offline',
        glpi: 'offline',
        glpi_message: 'Erro de conexão',
        glpi_response_time: 0,
        last_update: new Date().toISOString(),
        version: '1.0.0'
      };
    }
  }
};

// Função auxiliar para criar métricas padrão
function createDefaultMetrics(): DashboardMetrics {
  const defaultLevel = {
    novos: 0,
    pendentes: 0,
    progresso: 0,
    resolvidos: 0,
    total: 0
  };

  return {
    niveis: {
      n1: { ...defaultLevel },
      n2: { ...defaultLevel },
      n3: { ...defaultLevel },
      n4: { ...defaultLevel },
      geral: { ...defaultLevel }
    },
    tendencias: {
      novos: '0%',
      pendentes: '0%',
      progresso: '0%',
      resolvidos: '0%'
    },
    data_source: 'mock' as const,
    is_mock_data: true
  };
}