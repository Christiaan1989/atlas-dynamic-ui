import { useMemo } from "react";
import { Message } from "@langchain/langgraph-sdk";

export interface ClaimState {
  claimNumber: string | null;
  claimStatus: string | null;
  incidentType: string | null;
  severity: string | null;
  estimatedRange: string | null;
  midEstimate: string | null;
  customerDeductible: string | null;
  coveragePayout: string | null;
  exceedsLimit: boolean | null;
  decisionReason: string | null;
  /** Which steps have been completed */
  steps: {
    created: boolean;
    assessed: boolean;
    estimated: boolean;
    decided: boolean;
    reported: boolean;
  };
}

const INITIAL_STATE: ClaimState = {
  claimNumber: null,
  claimStatus: null,
  incidentType: null,
  severity: null,
  estimatedRange: null,
  midEstimate: null,
  customerDeductible: null,
  coveragePayout: null,
  exceedsLimit: null,
  decisionReason: null,
  steps: {
    created: false,
    assessed: false,
    estimated: false,
    decided: false,
    reported: false,
  },
};

function safeParse(content: unknown): Record<string, unknown> | null {
  try {
    if (typeof content === "string") return JSON.parse(content);
    if (typeof content === "object" && content !== null)
      return content as Record<string, unknown>;
  } catch {
    // ignore
  }
  return null;
}

/**
 * Parses claim-related tool messages from the stream to build
 * a real-time claim state object for display in the ClaimsView.
 */
export function useClaimState(messages: Message[]): ClaimState {
  return useMemo(() => {
    const state: ClaimState = { ...INITIAL_STATE, steps: { ...INITIAL_STATE.steps } };

    for (const msg of messages) {
      if (msg.type !== "tool") continue;
      const name = (msg as any).name as string | undefined;
      const data = safeParse(msg.content);
      if (!name || !data) continue;

      switch (name) {
        case "create_claim": {
          const claim = (data.claim ?? data) as Record<string, unknown>;
          if (claim.claim_number) state.claimNumber = String(claim.claim_number);
          if (claim.status) state.claimStatus = String(claim.status);
          state.steps.created = true;
          break;
        }
        case "log_damage_assessment": {
          const assessment = (data.assessment ?? data) as Record<string, unknown>;
          if (assessment.damage_type) state.incidentType = String(assessment.damage_type);
          if (assessment.severity) state.severity = String(assessment.severity);
          state.steps.assessed = true;
          break;
        }
        case "estimate_repair_cost": {
          if (data.estimated_range) state.estimatedRange = String(data.estimated_range);
          if (data.mid_estimate) state.midEstimate = String(data.mid_estimate);
          if (data.customer_deductible) state.customerDeductible = String(data.customer_deductible);
          if (data.estimated_coverage_payout) state.coveragePayout = String(data.estimated_coverage_payout);
          if (data.exceeds_limit !== undefined) state.exceedsLimit = Boolean(data.exceeds_limit);
          state.steps.estimated = true;
          break;
        }
        case "update_claim": {
          const claim = (data.claim ?? data) as Record<string, unknown>;
          if (claim.status) state.claimStatus = String(claim.status);
          if (claim.decision_reason) state.decisionReason = String(claim.decision_reason);
          if (claim.incident_type) state.incidentType = String(claim.incident_type);
          state.steps.decided = true;
          break;
        }
        case "generate_claim_report": {
          state.steps.reported = true;
          break;
        }
      }
    }

    return state;
  }, [messages]);
}
