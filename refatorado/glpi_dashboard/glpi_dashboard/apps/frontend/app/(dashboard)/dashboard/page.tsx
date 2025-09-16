import { DashboardLayout } from "../../components/layouts/DashboardLayout";
import { TicketsOverviewPanel } from "../../components/organisms/TicketsOverviewPanel";
import { TechnicianRankingBoard } from "../../components/organisms/TechnicianRankingBoard";
import { SlaTrendChart } from "../../components/organisms/SlaTrendChart";
import { SystemHealthPanel } from "../../components/organisms/SystemHealthPanel";
import styles from "./page.module.css";

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <TicketsOverviewPanel />
      <section className={styles.grid}>
        <TechnicianRankingBoard />
        <SlaTrendChart />
        <SystemHealthPanel />
      </section>
    </DashboardLayout>
  );
}
