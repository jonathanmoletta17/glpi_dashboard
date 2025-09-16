"use client";

import clsx from "clsx";
import styles from "./StatusBadge.module.css";

interface Props {
  status: "created" | "in_progress" | "pending" | "solved" | "closed" | string;
}

export function StatusBadge({ status }: Props) {
  return <span className={clsx(styles.badge, styles[status] ?? styles.default)}>{status}</span>;
}
