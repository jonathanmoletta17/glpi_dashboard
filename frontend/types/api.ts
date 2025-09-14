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
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp?: string;
}

export interface ApiError {
  success: false;
  error: string;
  details?: any;
  timestamp?: string;
  code?: string | number;
}