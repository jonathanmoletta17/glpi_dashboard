"""
Client and hooks for ticket metrics API.

Uses the Fetch API to retrieve aggregated ticket metrics from the backend and
react-query to expose a convenient hook. The base URL is assumed to be
configured via environment variables or defaults to the same origin.
"""

import { useQuery } from '@tanstack/react-query';

export async function fetchTicketMetrics(baseUrl: string = ''): Promise<any> {
  const res = await fetch(`${baseUrl}/tickets/metrics`);
  if (!res.ok) {
    throw new Error('Failed to fetch ticket metrics');
  }
  return res.json();
}

export function useTicketMetrics(baseUrl: string = '') {
  return useQuery(['ticketMetrics', baseUrl], () => fetchTicketMetrics(baseUrl));
}