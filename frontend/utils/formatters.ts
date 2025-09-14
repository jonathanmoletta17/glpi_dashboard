export function formatNumber(value: number): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toString();
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

export function formatDateTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function formatPercentage(value: string | number): string {
  if (typeof value === 'string') {
    return value.includes('%') ? value : `${value}%`;
  }
  return `${value}%`;
}

export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    novos: '#5A9BD4',
    progresso: '#F59E0B',
    pendentes: '#EF4444',
    resolvidos: '#10B981',
    new: '#5A9BD4',
    progress: '#F59E0B',
    pending: '#EF4444',
    resolved: '#10B981'
  };
  return statusColors[status.toLowerCase()] || '#6B7280';
}

export function getStatusBgColor(status: string): string {
  const statusBgColors: Record<string, string> = {
    novos: 'bg-[#5A9BD4]',
    progresso: 'bg-orange-500',
    pendentes: 'bg-amber-500',
    resolvidos: 'bg-green-500',
    new: 'bg-[#5A9BD4]',
    progress: 'bg-orange-500',
    pending: 'bg-amber-500',
    resolved: 'bg-green-500'
  };
  return statusBgColors[status.toLowerCase()] || 'bg-gray-500';
}