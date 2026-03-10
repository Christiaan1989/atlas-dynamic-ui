"use client";

import { motion } from "framer-motion";
import {
  FileText,
  Zap,
  Clock,
  ShieldAlert,
  DollarSign,
  TrendingUp,
} from "lucide-react";
import type { DashboardData } from "@/lib/dashboard-api";

interface KPICardsProps {
  data: DashboardData;
}

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export function KPICards({ data }: KPICardsProps) {
  const cards = [
    {
      label: "Total Claims",
      value: data.total_claims_30d,
      format: (v: number) => v.toLocaleString(),
      icon: FileText,
      color: "text-chart-1",
      bg: "bg-chart-1/10",
    },
    {
      label: "STP Rate",
      value: data.stp_rate,
      format: (v: number) => `${v.toFixed(1)}%`,
      icon: Zap,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
    },
    {
      label: "Avg Processing",
      value: data.avg_processing_seconds,
      format: (v: number) => (v < 60 ? `${v.toFixed(0)}s` : `${(v / 60).toFixed(1)}m`),
      icon: Clock,
      color: "text-chart-2",
      bg: "bg-chart-2/10",
    },
    {
      label: "Fraud Flags",
      value: data.fraud_high + data.fraud_medium,
      format: (v: number) => v.toLocaleString(),
      subtitle: `${data.fraud_high} high / ${data.fraud_medium} med`,
      icon: ShieldAlert,
      color: "text-destructive",
      bg: "bg-destructive/10",
    },
    {
      label: "Avg Repair Cost",
      value: data.avg_repair_cost,
      format: (v: number) =>
        `R${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
      icon: DollarSign,
      color: "text-chart-5",
      bg: "bg-chart-5/10",
    },
    {
      label: "Auto-Approved",
      value:
        data.claims_by_status.find((s) => s.status === "accepted")?.count ?? 0,
      format: (v: number) => v.toLocaleString(),
      icon: TrendingUp,
      color: "text-chart-4",
      bg: "bg-chart-4/10",
    },
  ];

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6"
    >
      {cards.map((card) => (
        <motion.div
          key={card.label}
          variants={item}
          className="group relative overflow-hidden rounded-xl border border-border bg-card p-4 transition-shadow hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {card.label}
            </span>
            <div className={`rounded-lg p-1.5 ${card.bg}`}>
              <card.icon className={`h-3.5 w-3.5 ${card.color}`} />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold tracking-tight text-foreground">
            {card.format(card.value)}
          </p>
          {card.subtitle && (
            <p className="mt-0.5 text-xs text-muted-foreground">
              {card.subtitle}
            </p>
          )}
          {/* subtle gradient accent */}
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-accent/40 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
        </motion.div>
      ))}
    </motion.div>
  );
}
