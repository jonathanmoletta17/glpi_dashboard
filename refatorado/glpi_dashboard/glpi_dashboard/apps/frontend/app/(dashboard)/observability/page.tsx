import { SlaTrendChart } from "../../components/organisms/SlaTrendChart";
import { SystemHealthPanel } from "../../components/organisms/SystemHealthPanel";
import styles from "./page.module.css";

export default function ObservabilityPage() {
  return (
    <section className={styles.wrapper}>
      <h2>Observabilidade</h2>
      <div className={styles.grid}>
        <SlaTrendChart />
        <SystemHealthPanel />
      </div>
    </section>
  );
}
