export interface LevelMetrics {
  novos: number;
  pendentes: number;
  progresso: number;
  resolvidos: number;
  total: number;
}

export interface DashboardMetrics {
  niveis: {
    n1: LevelMetrics;
    n2: LevelMetrics;
    n3: LevelMetrics;
    n4: LevelMetrics;
    geral: LevelMetrics;
  };
  tendencias?: {
    novos: string;
    pendentes: string;
    progresso: string;
    resolvidos: string;
  };
  timestamp?: string;
  systemStatus?: SystemStatus;
  // ← NOVOS CAMPOS PARA IDENTIFICAÇÃO DE FONTE
  data_source: 'glpi' | 'mock';
  is_mock_data: boolean;
}

export interface SystemStatus {
  api: string;
  glpi: string;
  glpi_message?: string;
  glpi_response_time?: number;
  last_update?: string;
  version?: string;
}

export interface TechnicianRanking {
  id: string;
  name: string;
  nome?: string;
  level: string;
  rank: number;
  total: number;
  score?: number;
  ticketsResolved?: number;
  ticketsInProgress?: number;
  averageResolutionTime?: number;
  // ← NOVOS CAMPOS PARA IDENTIFICAÇÃO DE FONTE
  data_source: 'glpi' | 'mock';
  is_mock_data: boolean;
}

export interface NewTicket {
  id: string;
  title: string;
  description: string;
  date: string;
  requester: string;
  priority: string;
  status: string;
  level?: string;
  // ← NOVOS CAMPOS PARA IDENTIFICAÇÃO DE FONTE
  data_source: 'glpi' | 'mock';
  is_mock_data: boolean;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp?: string;
  // ← NOVOS CAMPOS PARA IDENTIFICAÇÃO DE FONTE
  data_source: 'glpi' | 'mock';
  is_mock_data: boolean;
}

export interface ApiError {
  success: false;
  error: string;
  details?: any;
  timestamp?: string;
  code?: string | number;
}