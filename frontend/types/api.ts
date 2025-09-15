export interface LevelMetrics {
  novos: number;
  pendentes: number;
  progresso: number;
  resolvidos: number;
  total: number; // ← ADICIONADO: Campo obrigatório do backend
}

export interface NiveisMetrics {
  n1: LevelMetrics;
  n2: LevelMetrics;
  n3: LevelMetrics;
  n4: LevelMetrics;
}

export interface DashboardMetrics {
  // Estrutura de níveis (campo obrigatório)
  niveis: NiveisMetrics;
  
  // Campos obrigatórios de totais (alinhado com Pydantic)
  total: number;
  novos: number;
  pendentes: number;
  progresso: number;
  resolvidos: number;
  
  tendencias: {
    novos: string;
    pendentes: string;
    progresso: string;
    resolvidos: string;
  };
  
  timestamp: string;
  period_start?: string;
  period_end?: string;
  systemStatus?: SystemStatus;
  
  // Campos de identificação de fonte
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
  id: number;
  name: string;
  level: 'N1' | 'N2' | 'N3' | 'N4' | 'UNKNOWN'; // ← CORRIGIDO: Enum específico
  ticket_count: number; // ← CORRIGIDO: Campo do backend
  performance_score?: number; // ← ADICIONADO: Campo opcional do backend
  
  // Campos de compatibilidade (deprecated)
  rank?: number;
  total?: number;
  
  // Campos de identificação de fonte (obrigatórios)
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