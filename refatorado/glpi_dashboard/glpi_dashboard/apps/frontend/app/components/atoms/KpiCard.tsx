"use client";

import { ReactNode } from "react";
import { colors } from "../../design-system/tokens/colors";
import { spacing } from "../../design-system/tokens/spacing";
import { typography } from "../../design-system/tokens/typography";
import styles from "./KpiCard.module.css";

interface Props {
  label: string;
  value: ReactNode;
  helper?: string;
  tone?: "default" | "positive" | "negative";
}

export function KpiCard({ label, value, helper, tone = "default" }: Props) {
  return (
    <article className={`${styles.card} ${styles[tone]}`}>
      <header className={styles.header}>{label}</header>
      <div className={styles.value}>{value}</div>
      {helper && <footer className={styles.helper}>{helper}</footer>}
    </article>
  );
}
