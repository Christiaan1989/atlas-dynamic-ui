"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartTooltip } from "./ChartTooltip";
import type { ProcessingTimeBucket } from "@/lib/dashboard-api";

interface Props {
  data: ProcessingTimeBucket[];
}

export function ProcessingTimeChart({ data }: Props) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-foreground">
        Processing Time Distribution
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart
          data={data}
          margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="oklch(0.91 0.01 245)"
            vertical={false}
          />
          <XAxis
            dataKey="bucket"
            tick={{ fontSize: 11, fill: "oklch(0.45 0.02 245)" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "oklch(0.45 0.02 245)" }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip content={<ChartTooltip />} />
          <Bar
            dataKey="count"
            name="Claims"
            fill="oklch(0.25 0.06 245)"
            radius={[6, 6, 0, 0]}
            barSize={36}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
