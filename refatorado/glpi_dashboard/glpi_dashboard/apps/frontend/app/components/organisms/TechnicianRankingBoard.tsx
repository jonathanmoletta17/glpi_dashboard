"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchTechnicianRanking } from "../../services/metricsClient";
import { TechnicianLegend } from "../molecules/TechnicianLegend";
import styles from "./TechnicianRankingBoard.module.css";

export function TechnicianRankingBoard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["technician-ranking"],
    queryFn: fetchTechnicianRanking,
    staleTime: 300_000
  });

  if (isLoading) {
    return <section className="panel">Carregando ranking...</section>;
  }

  if (error || !data) {
    return <section className="panel">Erro ao carregar ranking.</section>;
  }

  return (
    <section className="panel">
      <header className={styles.header}>
        <div>
          <h3>Leaderboard de Técnicos</h3>
          <p>Eficiência ponderada por fechamentos e violações de SLA.</p>
        </div>
      </header>
      <TechnicianLegend data={data} />
    </section>
  );
}
