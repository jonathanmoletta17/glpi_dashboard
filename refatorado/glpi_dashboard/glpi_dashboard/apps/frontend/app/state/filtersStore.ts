"use client";

import { create } from "zustand";
import { immer } from "zustand/middleware/immer";

type TimeRange = "24h" | "7d" | "30d";

interface FiltersState {
  timeRange: TimeRange;
  setTimeRange: (range: TimeRange) => void;
}

export const useFiltersStore = create<FiltersState>()(
  immer((set) => ({
    timeRange: "24h",
    setTimeRange: (range) => set((state) => void (state.timeRange = range))
  }))
);
