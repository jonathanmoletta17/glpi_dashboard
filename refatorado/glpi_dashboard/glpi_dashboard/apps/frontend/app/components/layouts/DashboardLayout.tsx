import { PropsWithChildren } from "react";
import styles from "./DashboardLayout.module.css";

export function DashboardLayout({ children }: PropsWithChildren) {
  return <div className={styles.container}>{children}</div>;
}
