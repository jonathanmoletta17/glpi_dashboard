import { httpClient } from './httpClient';
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
      const response = await httpClient.get<ApiResponse<DashboardMetrics>>('/metrics');
      
      // Verificar se a resposta tem a estrutura esperada
      if (response.data?.data) {
        return response.data.data;
      } else if (response.data && 'niveis' in response.data) {
        // Resposta direta sem wrapper
        return response.data as unknown as DashboardMetrics;
      }
      
      // Fallback para estrutura padrão se não houver dados
      return createDefaultMetrics();
    } catch (error) {
      console.error('Erro ao buscar métricas:', error);
      // Retornar dados padrão em caso de erro
      return createDefaultMetrics();
    }
  },

  async getTechnicianRanking(): Promise<TechnicianRanking[]> {
    try {
      const response = await httpClient.get<ApiResponse<TechnicianRanking[]>>('/technicians/ranking');
      
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
      const response = await httpClient.get<ApiResponse<NewTicket[]>>('/tickets/new', {
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
      const response = await httpClient.get<ApiResponse<SystemStatus>>('/status');
      
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
    }
  };
}