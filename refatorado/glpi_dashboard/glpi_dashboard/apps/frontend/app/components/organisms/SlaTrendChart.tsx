"use client";

import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { fetchSlaSummary } from "../../services/metricsClient";
import styles from "./SlaTrendChart.module.css";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export function SlaTrendChart() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["sla-summary"],
    queryFn: fetchSlaSummary,
    staleTime: 60_000
  });

  if (isLoading) {
    return <section className="panel">Calculando violações...</section>;
  }

  if (error || !data) {
    return <section className="panel">Erro ao carregar violações.</section>;
  }

  const queues = Object.keys(data.breaches_by_queue);
  const counts = Object.values(data.breaches_by_queue);

  const option = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: queues },
    yAxis: { type: "value" },
    series: [
      {
        data: counts,
        type: "bar",
        itemStyle: {
          color: "#f87171"
        }
      }
    ]
  };

  return (
    <section className="panel">
      <header className={styles.header}>
        <div>
          <h3>Violações de SLA por Fila</h3>
          <p>{data.total_breaches} incidentes registrados.</p>
        </div>
      </header>
      <ReactECharts option={option} style={{ height: 260 }} />
      <footer className={styles.footer}>
        Últimas violações:
        <ul>
          {data.recent_breaches.map((breach) => (
            <li key={breach.ticket_id}>
              #{breach.ticket_id} • {breach.queue ?? "Sem fila"} • {breach.severity}
            </li>
          ))}
        </ul>
      </footer>
    </section>
  );
}
