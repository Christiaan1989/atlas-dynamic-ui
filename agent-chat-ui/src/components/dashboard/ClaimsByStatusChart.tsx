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
import type { ClaimsByStatus } from "@/lib/dashboard-api";

interface Props {
  data: ClaimsByStatus[];
}

const STATUS_COLORS: Record<string, string> = {
  accepted: "oklch(0.55 0.18 145)",
  denied: "oklch(0.577 0.245 27.325)",
  escalated: "oklch(0.68 0.14 85)",
  needs_info: "oklch(0.60 0.16 260)",
  intake: "oklch(0.75 0.10 200)",
};

export function ClaimsByStatusChart({ data }: Props) {
  const total = data.reduce((s, d) => s + d.count, 0);

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-foreground">
        Claims by Status
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="status"
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={3}
            strokeWidth={0}
          >
            {data.map((entry) => (
              <Cell
                key={entry.status}
                fill={STATUS_COLORS[entry.status] ?? "oklch(0.7 0.05 245)"}
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
                {value.replace("_", " ")}
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
      <p className="mt-1 text-center text-xs text-muted-foreground">
        {total} total claims
      </p>
    </div>
  );
}
