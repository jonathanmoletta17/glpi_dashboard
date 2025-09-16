"use client";

import styles from "./TicketsTable.module.css";
import type { QueueBacklogDTO } from "../../services/metricsClient";

interface Props {
  data: QueueBacklogDTO[];
}

export function TicketsTable({ data }: Props) {
  return (
    <table className={styles.table} aria-label="Backlog por fila">
      <thead>
        <tr>
          <th>Fila</th>
          <th>Quantidade</th>
        </tr>
      </thead>
      <tbody>
        {data.map((item) => (
          <tr key={item.queue}>
            <td>{item.queue}</td>
            <td>{item.count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
