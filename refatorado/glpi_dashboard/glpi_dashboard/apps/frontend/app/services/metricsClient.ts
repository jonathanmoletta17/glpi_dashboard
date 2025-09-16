const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type HttpMethod = "GET" | "POST";

class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

async function request<T>(path: string, method: HttpMethod = "GET"): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json"
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(`Erro ao acessar ${path}`, response.status);
  }

  return (await response.json()) as T;
}

export interface QueueBacklogDTO {
  queue: string;
  count: number;
}

export interface AgingBucketDTO {
  bucket: string;
  count: number;
}

export interface TicketsOverviewDTO {
  total_backlog: number;
  backlog_by_status: Record<string, number>;
  backlog_by_priority: Record<string, number>;
  backlog_by_queue: QueueBacklogDTO[];
  new_last_24h: number;
  new_last_7d: number;
  aging: AgingBucketDTO[];
  sla_breaches: number;
  average_resolution_minutes: number | null;
}

export interface TicketTimelineEventDTO {
  at: string;
  description: string;
  status: string;
}

export interface TicketTimelineDTO {
  events: TicketTimelineEventDTO[];
}

export interface TechnicianRankingEntryDTO {
  technician_id: number;
  name: string;
  tickets_handled: number;
  tickets_closed: number;
  sla_breaches: number;
  average_resolution_minutes: number | null;
  efficiency_score: number;
}

export interface SlaBreachDTO {
  ticket_id: number;
  technician: string | null;
  queue: string | null;
  breached_at: string;
  delay_minutes: number;
  severity: string;
}

export interface SlaSummaryDTO {
  total_breaches: number;
  breaches_by_queue: Record<string, number>;
  recent_breaches: SlaBreachDTO[];
}

export interface SystemHealthDTO {
  ingestion_lag_seconds: number | null;
  tickets_snapshot_at: string | null;
}

export async function fetchTicketsOverview(): Promise<TicketsOverviewDTO> {
  return request<TicketsOverviewDTO>("/v1/tickets/overview");
}

export async function fetchTicketTimeline(id: number): Promise<TicketTimelineDTO> {
  return request<TicketTimelineDTO>(`/v1/tickets/${id}/timeline`);
}

export async function fetchTechnicianRanking(): Promise<TechnicianRankingEntryDTO[]> {
  return request<TechnicianRankingEntryDTO[]>("/v1/technicians/ranking");
}

export async function fetchSlaSummary(): Promise<SlaSummaryDTO> {
  return request<SlaSummaryDTO>("/v1/sla/breaches");
}

export async function fetchSystemHealth(): Promise<SystemHealthDTO> {
  return request<SystemHealthDTO>("/v1/system/health");
}
