export interface ClaimsByStatus {
  status: string;
  count: number;
}

export interface ClaimsByType {
  incident_type: string;
  count: number;
}

export interface ClaimsTrendDay {
  date: string;
  accepted: number;
  denied: number;
  escalated: number;
  needs_info: number;
  intake: number;
}

export interface FraudBucket {
  level: string;
  count: number;
}

export interface ProcessingTimeBucket {
  bucket: string;
  count: number;
}

export interface RecentClaim {
  id: string;
  claim_number: string;
  status: string;
  incident_type: string | null;
  customer_name: string;
  fraud_risk_level: string | null;
  estimated_cost_mid: number | null;
  created_at: string;
}

export interface DashboardData {
  total_claims_30d: number;
  stp_rate: number;
  avg_processing_seconds: number;
  fraud_high: number;
  fraud_medium: number;
  fraud_low: number;
  avg_repair_cost: number;
  claims_by_status: ClaimsByStatus[];
  claims_by_type: ClaimsByType[];
  claims_trend: ClaimsTrendDay[];
  fraud_distribution: FraudBucket[];
  processing_time_buckets: ProcessingTimeBucket[];
  recent_claims: RecentClaim[];
}

const API_BASE = process.env.NEXT_PUBLIC_INSURANCE_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_INSURANCE_API_KEY || "demo-api-key-2025";

export async function fetchDashboard(): Promise<DashboardData> {
  const res = await fetch(`${API_BASE}/dashboard`, {
    headers: { "X-API-Key": API_KEY },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Dashboard fetch failed (${res.status})`);
  }
  return res.json();
}
