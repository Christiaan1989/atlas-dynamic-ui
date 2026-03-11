"use client";

import { useCallback, useEffect, useState } from "react";

// ---------------------------------------------------------------------------
// Types matching the backend API schemas
// ---------------------------------------------------------------------------
export interface Coverage {
  id: string;
  coverage_type: string;
  deductible_amount: number | null;
  limit_amount: number | null;
  max_severity: string | null;
}

export interface Customer {
  id: string;
  full_name: string;
  created_at: string;
  city: { id: string; name: string; province: string } | null;
}

export interface Policy {
  id: string;
  policy_number: string;
  status: string;
  start_date: string;
  end_date: string;
  customer: Customer;
  coverages: Coverage[];
}

export interface ClaimSummary {
  id: string;
  claim_number: string;
  status: string;
  incident_date: string | null;
  incident_type: string | null;
  description: string;
  fraud_risk_level: string | null;
  fraud_risk_score: number | null;
  estimated_cost_min: number | null;
  estimated_cost_max: number | null;
  created_at: string;
}

export interface PolicyDashboardData {
  policy: Policy;
  claims: ClaimSummary[];
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------
const API_BASE =
  process.env.NEXT_PUBLIC_INSURANCE_API_URL || "http://localhost:8000";
const API_KEY =
  process.env.NEXT_PUBLIC_INSURANCE_API_KEY || "demo-api-key-2025";

const headers = { "X-API-Key": API_KEY };

async function fetchPolicyDashboard(
  policyNumber: string,
): Promise<PolicyDashboardData> {
  const [policyRes, claimsRes] = await Promise.all([
    fetch(`${API_BASE}/policies/${policyNumber}`, { headers, cache: "no-store" }),
    fetch(`${API_BASE}/policies/${policyNumber}/claims`, {
      headers,
      cache: "no-store",
    }),
  ]);

  if (!policyRes.ok) {
    throw new Error(`Policy fetch failed (${policyRes.status})`);
  }
  if (!claimsRes.ok) {
    throw new Error(`Claims fetch failed (${claimsRes.status})`);
  }

  const policy: Policy = await policyRes.json();
  const claims: ClaimSummary[] = await claimsRes.json();

  return { policy, claims };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
export function usePolicyDashboard(policyNumber: string) {
  const [data, setData] = useState<PolicyDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!policyNumber?.trim()) {
      setLoading(false);
      setError("No policy number provided");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const d = await fetchPolicyDashboard(policyNumber.trim());
      setData(d);
    } catch (e: any) {
      setError(e?.message ?? "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, [policyNumber]);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, refresh: load };
}
