// Placeholder metrics client using fetch API
export async function fetchMetrics() {
  const res = await fetch('/api/metrics');
  return res.json();
}
