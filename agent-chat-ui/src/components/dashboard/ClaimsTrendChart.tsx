"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartTooltip } from "./ChartTooltip";
import type { ClaimsTrendDay } from "@/lib/dashboard-api";

interface Props {
  data: ClaimsTrendDay[];
}

export function ClaimsTrendChart({ data }: Props) {
  // Simplify date labels
  const formatted = data.map((d) => ({
    ...d,
    label: new Date(d.date).toLocaleDateString("en-ZA", {
      day: "numeric",
      month: "short",
    }),
  }));

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-foreground">
        Claims Trend
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart
          data={formatted}
          margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
        >
          <defs>
            <linearGradient id="gradAccepted" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor="oklch(0.55 0.18 145)"
                stopOpacity={0.3}
              />
              <stop
                offset="100%"
                stopColor="oklch(0.55 0.18 145)"
                stopOpacity={0}
              />
            </linearGradient>
            <linearGradient id="gradDenied" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor="oklch(0.577 0.245 27.325)"
                stopOpacity={0.3}
              />
              <stop
                offset="100%"
                stopColor="oklch(0.577 0.245 27.325)"
                stopOpacity={0}
              />
            </linearGradient>
            <linearGradient id="gradEscalated" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor="oklch(0.68 0.14 85)"
                stopOpacity={0.3}
              />
              <stop
                offset="100%"
                stopColor="oklch(0.68 0.14 85)"
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="oklch(0.91 0.01 245)"
            vertical={false}
          />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10, fill: "oklch(0.45 0.02 245)" }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 10, fill: "oklch(0.45 0.02 245)" }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip content={<ChartTooltip />} />
          <Area
            type="monotone"
            dataKey="accepted"
            name="Accepted"
            stroke="oklch(0.55 0.18 145)"
            fill="url(#gradAccepted)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="denied"
            name="Denied"
            stroke="oklch(0.577 0.245 27.325)"
            fill="url(#gradDenied)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="escalated"
            name="Escalated"
            stroke="oklch(0.68 0.14 85)"
            fill="url(#gradEscalated)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
