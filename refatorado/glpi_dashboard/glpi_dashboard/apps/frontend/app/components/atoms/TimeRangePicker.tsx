"use client";

import { useState } from "react";
import styles from "./TimeRangePicker.module.css";

type Range = "24h" | "7d" | "30d";

interface Props {
  value?: Range;
  onChange?: (value: Range) => void;
}

const ranges: Range[] = ["24h", "7d", "30d"];

export function TimeRangePicker({ value = "24h", onChange }: Props) {
  const [selected, setSelected] = useState<Range>(value);

  function handleSelect(range: Range) {
    setSelected(range);
    onChange?.(range);
  }

  return (
    <div className={styles.wrapper} role="radiogroup" aria-label="Intervalo de tempo">
      {ranges.map((range) => (
        <button
          key={range}
          type="button"
          role="radio"
          aria-checked={selected === range}
          className={selected === range ? styles.active : styles.option}
          onClick={() => handleSelect(range)}
        >
          {range}
        </button>
      ))}
    </div>
  );
}
