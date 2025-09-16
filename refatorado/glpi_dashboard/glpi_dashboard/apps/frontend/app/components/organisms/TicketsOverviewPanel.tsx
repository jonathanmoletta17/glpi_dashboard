"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchTicketsOverview } from "../../services/metricsClient";
import { useFiltersStore } from "../../state/filtersStore";
import { KpiCard } from "../atoms/KpiCard";
import { TimeRangePicker } from "../atoms/TimeRangePicker";
import { TicketsTable } from "../molecules/TicketsTable";
import styles from "./TicketsOverviewPanel.module.css";

export function TicketsOverviewPanel() {
  const timeRange = useFiltersStore((state) => state.timeRange);
  const setTimeRange = useFiltersStore((state) => state.setTimeRange);

  const { data, isLoading, error } = useQuery({
    queryKey: ["tickets-overview"],
    queryFn: fetchTicketsOverview,
    staleTime: 30_000
  });

  if (isLoading) {
    return <section className={styles.panel}>Carregando métricas...</section>;
  }

  if (error || !data) {
    return <section className={styles.panel}>Erro ao carregar métricas.</section>;
  }

  return (
    <section className={styles.panel}>
      <header className={styles.header}>
        <div>
          <h2>Visão Geral de Tickets</h2>
          <p>Métricas calculadas a partir da última sincronização com o GLPI.</p>
        </div>
        <TimeRangePicker value={timeRange} onChange={setTimeRange} />
      </header>
      <div className={styles.kpis}>
        <KpiCard label="Backlog" value={data.total_backlog} helper="Tickets abertos" />
        <KpiCard label="Novos (24h)" value={data.new_last_24h} helper="Entradas recentes" />
        <KpiCard label="Novos (7d)" value={data.new_last_7d} helper="Últimos 7 dias" />
        <KpiCard
          label="SLA Violado"
          value={data.sla_breaches}
          helper="Soma total"
          tone={data.sla_breaches > 0 ? "negative" : "positive"}
        />
      </div>
      <div className={styles.grid}>
        <div className="panel">
          <h3>Aging do Backlog</h3>
          <ul className={styles.agingList}>
            {data.aging.map((bucket) => (
              <li key={bucket.bucket}>
                <span>{bucket.bucket}</span>
                <strong>{bucket.count}</strong>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h3>Backlog por Fila</h3>
          <TicketsTable data={data.backlog_by_queue} />
        </div>
      </div>
    </section>
  );
}
