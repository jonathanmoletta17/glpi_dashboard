"use client";

import styles from "./TechnicianLegend.module.css";
import type { TechnicianRankingEntryDTO } from "../../services/metricsClient";

interface Props {
  data: TechnicianRankingEntryDTO[];
}

export function TechnicianLegend({ data }: Props) {
  return (
    <ul className={styles.list} aria-label="Ranking de técnicos">
      {data.map((item) => (
        <li key={item.technician_id} className={styles.item}>
          <div>
            <strong>{item.name}</strong>
            <span>{item.tickets_closed} fechados • SLA {item.sla_breaches}</span>
          </div>
          <span className={styles.score}>{item.efficiency_score.toFixed(2)}</span>
        </li>
      ))}
    </ul>
  );
}
