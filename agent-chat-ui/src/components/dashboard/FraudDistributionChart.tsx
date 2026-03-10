"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { ChartTooltip } from "./ChartTooltip";
import type { FraudBucket } from "@/lib/dashboard-api";

interface Props {
  data: FraudBucket[];
}

const FRAUD_COLORS: Record<string, string> = {
  high: "oklch(0.577 0.245 27.325)",
  medium: "oklch(0.68 0.14 85)",
  low: "oklch(0.55 0.18 145)",
};

export function FraudDistributionChart({ data }: Props) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-foreground">
        Fraud Risk Distribution
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="level"
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={3}
            strokeWidth={0}
          >
            {data.map((entry) => (
              <Cell
                key={entry.level}
                fill={FRAUD_COLORS[entry.level] ?? "oklch(0.7 0.05 245)"}
              />
            ))}
          </Pie>
          <Tooltip content={<ChartTooltip />} />
          <Legend
            verticalAlign="bottom"
            iconType="circle"
            iconSize={8}
            formatter={(value: string) => (
              <span className="text-xs capitalize text-muted-foreground">
                {value} risk
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
