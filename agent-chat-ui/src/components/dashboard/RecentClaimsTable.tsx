"use client";

import { motion } from "framer-motion";
import type { RecentClaim } from "@/lib/dashboard-api";

interface Props {
  data: RecentClaim[];
}

const STATUS_BADGE: Record<string, string> = {
  accepted:
    "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  denied:
    "bg-red-500/10 text-red-600 border-red-500/20",
  escalated:
    "bg-amber-500/10 text-amber-600 border-amber-500/20",
  needs_info:
    "bg-blue-500/10 text-blue-600 border-blue-500/20",
  intake:
    "bg-slate-500/10 text-slate-600 border-slate-500/20",
};

const FRAUD_BADGE: Record<string, string> = {
  high: "bg-red-500/10 text-red-600",
  medium: "bg-amber-500/10 text-amber-600",
  low: "bg-emerald-500/10 text-emerald-600",
};

export function RecentClaimsTable({ data }: Props) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-foreground">
        Recent Claims
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
              <th className="pb-2 pr-4 font-medium">Claim #</th>
              <th className="pb-2 pr-4 font-medium">Customer</th>
              <th className="pb-2 pr-4 font-medium">Type</th>
              <th className="pb-2 pr-4 font-medium">Status</th>
              <th className="pb-2 pr-4 font-medium">Fraud Risk</th>
              <th className="pb-2 pr-4 font-medium text-right">
                Est. Cost
              </th>
              <th className="pb-2 font-medium text-right">Filed</th>
            </tr>
          </thead>
          <tbody>
            {data.map((claim, i) => (
              <motion.tr
                key={claim.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="border-b border-border/50 last:border-0"
              >
                <td className="py-2.5 pr-4 font-mono text-xs font-medium text-foreground">
                  {claim.claim_number}
                </td>
                <td className="py-2.5 pr-4 text-foreground">
                  {claim.customer_name}
                </td>
                <td className="py-2.5 pr-4 capitalize text-muted-foreground">
                  {claim.incident_type ?? "N/A"}
                </td>
                <td className="py-2.5 pr-4">
                  <span
                    className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold capitalize ${STATUS_BADGE[claim.status] ?? STATUS_BADGE.intake}`}
                  >
                    {claim.status.replace("_", " ")}
                  </span>
                </td>
                <td className="py-2.5 pr-4">
                  {claim.fraud_risk_level ? (
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize ${FRAUD_BADGE[claim.fraud_risk_level] ?? ""}`}
                    >
                      {claim.fraud_risk_level}
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground">-</span>
                  )}
                </td>
                <td className="py-2.5 pr-4 text-right font-mono text-xs text-foreground">
                  {claim.estimated_cost_mid
                    ? `R${claim.estimated_cost_mid.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                    : "-"}
                </td>
                <td className="py-2.5 text-right text-xs text-muted-foreground">
                  {new Date(claim.created_at).toLocaleDateString("en-ZA", {
                    day: "numeric",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
