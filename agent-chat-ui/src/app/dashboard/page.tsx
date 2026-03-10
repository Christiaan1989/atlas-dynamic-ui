"use client";

import { useDashboard } from "@/hooks/use-dashboard";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { KPICards } from "@/components/dashboard/KPICards";
import { ClaimsTrendChart } from "@/components/dashboard/ClaimsTrendChart";
import { ClaimsByStatusChart } from "@/components/dashboard/ClaimsByStatusChart";
import { ClaimsByTypeChart } from "@/components/dashboard/ClaimsByTypeChart";
import { FraudDistributionChart } from "@/components/dashboard/FraudDistributionChart";
import { ProcessingTimeChart } from "@/components/dashboard/ProcessingTimeChart";
import { RecentClaimsTable } from "@/components/dashboard/RecentClaimsTable";

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* KPI row skeleton */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-24 animate-pulse rounded-xl border border-border bg-card"
          />
        ))}
      </div>
      {/* Chart skeletons */}
      <div className="h-72 animate-pulse rounded-xl border border-border bg-card" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="h-64 animate-pulse rounded-xl border border-border bg-card"
          />
        ))}
      </div>
      <div className="h-56 animate-pulse rounded-xl border border-border bg-card" />
      <div className="h-80 animate-pulse rounded-xl border border-border bg-card" />
    </div>
  );
}

function ErrorBanner({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-destructive/30 bg-destructive/5 p-12">
      <p className="text-sm font-medium text-destructive">{message}</p>
      <button
        onClick={onRetry}
        className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Try Again
      </button>
    </div>
  );
}

export default function DashboardPage() {
  const { data, loading, error, refresh } = useDashboard();

  return (
    <DashboardShell loading={loading} onRefresh={refresh}>
      {loading && !data && <DashboardSkeleton />}

      {error && !data && <ErrorBanner message={error} onRetry={refresh} />}

      {data && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <KPICards data={data} />

          {/* Claims Trend (full width) */}
          <ClaimsTrendChart data={data.claims_trend} />

          {/* Three charts in a row */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            <ClaimsByStatusChart data={data.claims_by_status} />
            <FraudDistributionChart data={data.fraud_distribution} />
            <ClaimsByTypeChart data={data.claims_by_type} />
          </div>

          {/* Processing time (full width) */}
          <ProcessingTimeChart data={data.processing_time_buckets} />

          {/* Recent Claims table */}
          <RecentClaimsTable data={data.recent_claims} />
        </div>
      )}
    </DashboardShell>
  );
}
