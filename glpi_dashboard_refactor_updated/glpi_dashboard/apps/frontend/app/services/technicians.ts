"""
Client and hooks for technician performance API.
"""

import { useQuery } from '@tanstack/react-query';

export async function fetchTechnicianPerformance(baseUrl: string = ''): Promise<any> {
  const res = await fetch(`${baseUrl}/tickets/technicians/performance`);
  if (!res.ok) {
    throw new Error('Failed to fetch technician performance');
  }
  return res.json();
}

export function useTechnicianPerformance(baseUrl: string = '') {
  return useQuery(['technicianPerformance', baseUrl], () => fetchTechnicianPerformance(baseUrl));
}