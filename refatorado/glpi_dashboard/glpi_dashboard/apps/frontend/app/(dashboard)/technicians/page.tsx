import { TechnicianRankingBoard } from "../../components/organisms/TechnicianRankingBoard";
import styles from "./page.module.css";

export default function TechniciansPage() {
  return (
    <section className={styles.wrapper}>
      <h2>Desempenho de Técnicos</h2>
      <TechnicianRankingBoard />
    </section>
  );
}
