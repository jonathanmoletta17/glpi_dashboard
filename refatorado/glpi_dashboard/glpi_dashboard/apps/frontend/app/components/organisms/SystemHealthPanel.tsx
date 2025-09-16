"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchSystemHealth } from "../../services/metricsClient";
import styles from "./SystemHealthPanel.module.css";

export function SystemHealthPanel() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["system-health"],
    queryFn: fetchSystemHealth,
    refetchInterval: 60_000
  });

  if (isLoading) {
    return <section className="panel">Verificando integridade...</section>;
  }

  if (error || !data) {
    return <section className="panel">Erro ao consultar integridade.</section>;
  }

  const lag = data.ingestion_lag_seconds ?? 0;
  const status = lag > 600 ? "Crítico" : lag > 180 ? "Atenção" : "Saudável";

  return (
    <section className="panel">
      <header className={styles.header}>
        <div>
          <h3>Saúde Operacional</h3>
          <p>Lag de ingestão e sincronização dos dados.</p>
        </div>
      </header>
      <div className={styles.metrics}>
        <div>
          <span className={styles.label}>Lag de Ingestão</span>
          <strong>{lag.toFixed(0)}s</strong>
        </div>
        <div>
          <span className={styles.label}>Última Sincronização</span>
          <strong>{data.tickets_snapshot_at ?? "n/d"}</strong>
        </div>
        <div>
          <span className={styles.label}>Status</span>
          <strong>{status}</strong>
        </div>
      </div>
    </section>
  );
}
