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
import type { ClaimsByType } from "@/lib/dashboard-api";

interface Props {
  data: ClaimsByType[];
}

const TYPE_COLORS: Record<string, string> = {
  collision: "oklch(0.25 0.06 245)",
  theft: "oklch(0.577 0.245 27.325)",
  weather: "oklch(0.60 0.16 260)",
  glass: "oklch(0.68 0.14 85)",
  unknown: "oklch(0.7 0.05 245)",
};

export function ClaimsByTypeChart({ data }: Props) {
  const sorted = [...data].sort((a, b) => b.count - a.count);

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-foreground">
        Claims by Incident Type
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart
          data={sorted}
          layout="vertical"
          margin={{ top: 0, right: 12, bottom: 0, left: 0 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="oklch(0.91 0.01 245)"
            horizontal={false}
          />
          <XAxis
            type="number"
            tick={{ fontSize: 10, fill: "oklch(0.45 0.02 245)" }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <YAxis
            type="category"
            dataKey="incident_type"
            tick={{ fontSize: 11, fill: "oklch(0.45 0.02 245)" }}
            axisLine={false}
            tickLine={false}
            width={70}
            tickFormatter={(v: string) =>
              v.charAt(0).toUpperCase() + v.slice(1)
            }
          />
          <Tooltip content={<ChartTooltip />} />
          <Bar
            dataKey="count"
            name="Claims"
            radius={[0, 6, 6, 0]}
            barSize={20}
            fill="oklch(0.25 0.06 245)"
          >
            {sorted.map((entry) => (
              <rect
                key={entry.incident_type}
                fill={
                  TYPE_COLORS[entry.incident_type] ?? "oklch(0.7 0.05 245)"
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
