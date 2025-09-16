import { useQuery } from "@tanstack/react-query";
import { fetchTicketsOverview, fetchTicketTimeline } from "../../services/metricsClient";
import { TicketsTable } from "../../components/molecules/TicketsTable";
import { StatusBadge } from "../../components/atoms/StatusBadge";
import styles from "./page.module.css";

export default function TicketsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["tickets-overview"],
    queryFn: fetchTicketsOverview
  });

  if (isLoading) {
    return <section className={styles.wrapper}>Carregando tickets...</section>;
  }

  if (error || !data) {
    return <section className={styles.wrapper}>Erro ao carregar tickets.</section>;
  }

  return (
    <section className={styles.wrapper}>
      <h2>Backlog por Fila</h2>
      <TicketsTable data={data.backlog_by_queue} />
      <p className={styles.helper}>
        Utilize os filtros globais para correlacionar com fila, categoria e prioridade. Os detalhes de cada ticket são exibidos
        ao selecionar a linha correspondente.
      </p>
    </section>
  );
}
