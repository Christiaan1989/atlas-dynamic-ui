"""Tools for the Atlas V2 Claims Triage Agent.

Each tool wraps an HTTP call to the Mock Insurance Core API.
"""

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from langchain_core.tools import tool

API_URL = os.getenv("INSURANCE_API_URL", "http://localhost:8000")

_VECTOR_STORE_PATH = str(
    Path(__file__).resolve().parent.parent / "vector_store_2026_insurance.pkl"
)
_vector_store = None


def _get_vector_store():
    """Lazy-load the FAISS vector store so it's only read from disk once."""
    global _vector_store
    if _vector_store is None:
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings

        _vector_store = FAISS.load_local(
            _VECTOR_STORE_PATH,
            OpenAIEmbeddings(model="text-embedding-3-large"),
            allow_dangerous_deserialization=True,
        )
    return _vector_store

API_KEY = os.getenv("INSURANCE_API_KEY", "demo-api-key-2025")

_HEADERS = {"X-API-Key": API_KEY}


def _url(path: str) -> str:
    return f"{API_URL}{path}"


def _error(resp: httpx.Response) -> str:
    try:
        detail = resp.json().get("detail", resp.text)
    except Exception:
        detail = resp.text
    return json.dumps({"error": detail, "status_code": resp.status_code})


# ---------------------------------------------------------------------------
# UI view management (frontend-facing, no HTTP call)
# ---------------------------------------------------------------------------
@tool
def set_active_view(view: str) -> str:
    """Switch the customer portal UI to a specific full-screen view.

    Call this to change what the customer sees on screen. The view transition
    is animated and immediate.

    IMPORTANT: Only call this when the context clearly warrants a view change.
    Do NOT call this on every message.

    Args:
        view: The view to switch to. Must be one of:
              - "home" — the landing/welcome screen
              - "policy_qa" — the policy questions & answers view
              - "claims" — the guided claims filing experience
              - "coverage_upgrade" — the coverage upgrade options view
              - "damage_assessment" — the standalone damage assessment scanner
    """
    valid_views = {"home", "policy_qa", "claims", "coverage_upgrade", "damage_assessment"}
    if view not in valid_views:
        return json.dumps({"error": f"Invalid view '{view}'. Must be one of: {', '.join(sorted(valid_views))}"})
    return json.dumps({"active_view": view, "status": "ok"})


# ---------------------------------------------------------------------------
# Policy document retrieval (RAG)
# ---------------------------------------------------------------------------
@tool
def lookup_policy_info(query: str) -> str:
    """Search the company's insurance policy documents for relevant information.

    Use this when a customer asks general questions about how our policies
    work, what is covered or excluded, deductibles, claim procedures, terms
    and conditions, or any other policy-related question.

    This does NOT look up a specific customer's policy — use `get_policy`
    for that. This searches the company's published policy documentation.

    Args:
        query: The customer's question or topic to search for
              (e.g. "What does comprehensive coverage include?").
    """
    store = _get_vector_store()
    docs = store.similarity_search(query, k=4)
    if not docs:
        return json.dumps({"result": "No relevant policy information found."})
    results = []
    for i, doc in enumerate(docs, 1):
        results.append(f"--- Excerpt {i} ---\n{doc.page_content}")
    return "\n\n".join(results)


# ---------------------------------------------------------------------------
# Policy lookup
# ---------------------------------------------------------------------------
@tool
def get_policy(policy_number: str) -> str:
    """Look up an insurance policy by its policy number.

    Returns policy details including customer info, status, dates, and
    all coverage types (collision, comprehensive, liability, roadside).

    Use this FIRST when a customer provides their policy number so you
    can verify the policy is active and check what coverages they have.

    Args:
        policy_number: The policy number to look up (e.g. 'POL-ACTIVE-001').
    """
    resp = httpx.get(_url(f"/policies/{policy_number}"), headers=_HEADERS, timeout=10)
    if resp.status_code != 200:
        return _error(resp)
    return resp.text


# ---------------------------------------------------------------------------
# Customer city management (for recommendations)
# ---------------------------------------------------------------------------
@tool
def set_customer_city(customer_id: str, city_name: str) -> str:
    """Set the customer's city by name (South Africa cities only).

    Use this to record the policyholder's city so we can recommend nearby
    approved repair shops once a claim is accepted.

    Args:
        customer_id: UUID of the customer (from policy lookup)
        city_name: City name (e.g., 'Cape Town', 'Johannesburg')
    """
    resp = httpx.patch(
        _url(f"/customers/{customer_id}/city"),
        headers=_HEADERS,
        params={"city_name": city_name},
        timeout=10,
    )
    if resp.status_code != 200:
        return _error(resp)
    return resp.text


# ---------------------------------------------------------------------------
# Claim CRUD
# ---------------------------------------------------------------------------
@tool
def create_claim(
    policy_number: str,
    description: str,
    incident_date: Optional[str] = None,
    incident_type: Optional[str] = None,
) -> str:
    """Create a new insurance claim (FNOL — First Notice of Loss).

    Call this early in the conversation once you have the policy number
    and an initial description of what happened. You can enrich the
    claim later with update_claim.

    Args:
        policy_number: The policy number to file the claim against.
        description: Free-text description of the incident.
        incident_date: Date of the incident in YYYY-MM-DD format (optional).
        incident_type: One of collision, theft, weather, glass, unknown (optional).
    """
    body: dict[str, Any] = {
        "policy_number": policy_number,
        "description": description,
    }
    if incident_date:
        body["incident_date"] = incident_date
    if incident_type:
        body["incident_type"] = incident_type

    resp = httpx.post(_url("/claims"), json=body, headers=_HEADERS, timeout=10)
    if resp.status_code != 200:
        return _error(resp)
    return resp.text


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
@tool
def get_recommended_repair_shops(claim_id: str) -> str:
    """Get up to 4 approved repair shops for an ACCEPTED claim.

    Returns a nicely formatted list including name, contact details, and
    the insurer's rating. Only works if the claim status is 'accepted'.
    """
    resp = httpx.get(
        _url(f"/claims/{claim_id}/recommended-shops"), headers=_HEADERS, timeout=10
    )
    if resp.status_code != 200:
        return _error(resp)
    shops = resp.json()
    if not shops:
        return json.dumps({"result": "No approved shops found for the customer's city."})

    lines = [
        "Here are up to 4 approved repair shops in your area:",
        "",
    ]
    for i, s in enumerate(shops, 1):
        rating = "★" * int(s.get("rating", 0)) + "☆" * (5 - int(s.get("rating", 0)))
        email = s.get("email") or "N/A"
        lines.append(
            f"{i}. {s['name']}\n   Rating: {rating}  ({s.get('rating', 'N/A')}/5)\n   Phone: {s['phone']}\n   Email: {email}\n   Address: {s['address']}"
        )
    return "\n".join(lines)


@tool
def get_claim(claim_id: str) -> str:
    """Retrieve an existing claim by its UUID, including all audit events.

    Args:
        claim_id: The UUID of the claim.
    """
    resp = httpx.get(_url(f"/claims/{claim_id}"), headers=_HEADERS, timeout=10)
    if resp.status_code != 200:
        return _error(resp)
    return resp.text


@tool
def update_claim(
    claim_id: str,
    status: Optional[str] = None,
    incident_date: Optional[str] = None,
    incident_type: Optional[str] = None,
    decision_reason: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """Update fields on an existing claim.

    Use this to set the final decision (status + decision_reason) or to
    enrich fields like incident_date / incident_type after gathering info
    from the customer.

    Args:
        claim_id: The UUID of the claim to update.
        status: New status — one of intake, needs_info, accepted, denied, escalated.
        incident_date: Date of the incident in YYYY-MM-DD format.
        incident_type: One of collision, theft, weather, glass, unknown.
        decision_reason: Short plain-language reason for the decision.
        description: Updated FNOL narrative if the customer clarified.
    """
    body: dict[str, Any] = {}
    if status is not None:
        body["status"] = status
    if incident_date is not None:
        body["incident_date"] = incident_date
    if incident_type is not None:
        body["incident_type"] = incident_type
    if decision_reason is not None:
        body["decision_reason"] = decision_reason
    if description is not None:
        body["description"] = description

    resp = httpx.patch(_url(f"/claims/{claim_id}"), json=body, headers=_HEADERS, timeout=10)
    if resp.status_code != 200:
        return _error(resp)
    return resp.text


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------
@tool
def log_event(
    claim_id: str,
    event_type: str,
    message: str,
    payload: Optional[str] = None,
) -> str:
    """Write an audit event to the claim's event log.

    Use this to record every significant step:
    - Questions you ask the customer (event_type='question')
    - Answers the customer provides (event_type='answer')
    - Policy lookup results (event_type='tool_result')
    - Your final decision and the rule that triggered it (event_type='decision')
    - Any errors encountered (event_type='error')

    Args:
        claim_id: The UUID of the claim.
        event_type: One of note, question, answer, tool_result, decision, error, status_change.
        message: Human-readable description of the event.
        payload: Optional JSON string with structured data.
    """
    body: dict[str, Any] = {
        "event_type": event_type,
        "message": message,
    }
    if payload:
        try:
            body["payload"] = json.loads(payload)
        except json.JSONDecodeError:
            body["payload"] = {"raw": payload}

    resp = httpx.post(_url(f"/claims/{claim_id}/events"), json=body, headers=_HEADERS, timeout=10)
    if resp.status_code != 200:
        return _error(resp)
    return resp.text


# ---------------------------------------------------------------------------
# Photo damage assessment
# ---------------------------------------------------------------------------
@tool
def log_damage_assessment(
    claim_id: str,
    damage_type: str,
    severity: str,
    description_match: bool,
    details: str,
) -> str:
    """Log a photo damage assessment to the claim's audit trail.

    Call this AFTER the customer uploads a damage photo and you have
    analysed it. This records your visual assessment as a structured
    audit event on the claim.

    Args:
        claim_id: The UUID of the claim.
        damage_type: What the photo shows — one of collision, theft, weather, glass, unclear.
        severity: Estimated severity — one of minor, moderate, severe.
        description_match: True if the photo is consistent with the customer's description, False if not.
        details: Plain-language summary of what you see in the photo (e.g. "Rear bumper has a small dent approximately 10cm wide, paint scratched but no structural damage").
    """
    payload = {
        "damage_type": damage_type,
        "severity": severity,
        "description_match": description_match,
        "details": details,
    }
    body = {
        "event_type": "tool_result",
        "message": f"Photo damage assessment: {damage_type} ({severity}). Match with description: {description_match}.",
        "payload": payload,
    }
    resp = httpx.post(
        _url(f"/claims/{claim_id}/events"), json=body, headers=_HEADERS, timeout=10
    )
    if resp.status_code != 200:
        return _error(resp)
    return resp.text


# ---------------------------------------------------------------------------
# Fraud detection
# ---------------------------------------------------------------------------
@tool
def check_fraud_indicators(
    claim_id: str,
    policy_number: str,
    incident_date: str,
    description: str,
) -> str:
    """Run basic fraud indicator checks on a claim and log the results.

    Call this AFTER creating the claim and BEFORE making a final decision.
    It checks for common fraud red flags and returns a risk assessment.

    Args:
        claim_id: The UUID of the claim.
        policy_number: The policy number for this claim.
        incident_date: The incident date in YYYY-MM-DD format.
        description: The customer's description of the incident.
    """
    flags: list[str] = []
    score = 0

    # 1. Get policy to check start date
    policy_resp = httpx.get(_url(f"/policies/{policy_number}"), headers=_HEADERS, timeout=10)
    if policy_resp.status_code == 200:
        policy_data = policy_resp.json()
        policy_start = date.fromisoformat(policy_data["start_date"])
        incident_dt = date.fromisoformat(incident_date)
        days_since_start = (incident_dt - policy_start).days
        if days_since_start < 90:
            flags.append(f"NEW_POLICY: Policy started only {days_since_start} days before incident")
            score += 30

    # 2. Check for prior claims on this policy
    claims_resp = httpx.get(_url(f"/policies/{policy_number}/claims"), headers=_HEADERS, timeout=10)
    if claims_resp.status_code == 200:
        prior_claims = claims_resp.json()
        # Exclude the current claim from the count
        other_claims = [c for c in prior_claims if c["id"] != claim_id]
        if len(other_claims) >= 2:
            flags.append(f"FREQUENT_CLAIMANT: {len(other_claims)} prior claims on this policy")
            score += 25
        elif len(other_claims) == 1:
            flags.append(f"REPEAT_CLAIMANT: 1 prior claim on this policy")
            score += 10

    # 3. Check if incident was on a weekend
    incident_dt = date.fromisoformat(incident_date)
    if incident_dt.weekday() >= 5:
        day_name = "Saturday" if incident_dt.weekday() == 5 else "Sunday"
        flags.append(f"WEEKEND_INCIDENT: Incident occurred on a {day_name}")
        score += 15

    # 4. Check for vague description
    if len(description.strip()) < 20:
        flags.append("VAGUE_DESCRIPTION: Customer provided very brief description")
        score += 20

    # Determine risk level
    if score >= 50:
        risk_level = "high"
    elif score >= 25:
        risk_level = "medium"
    else:
        risk_level = "low"

    result = {
        "risk_score": score,
        "risk_level": risk_level,
        "flags": flags if flags else ["No fraud indicators detected"],
    }

    # Log to audit trail
    body = {
        "event_type": "tool_result",
        "message": f"Fraud check: risk_level={risk_level}, score={score}/100.",
        "payload": result,
    }
    httpx.post(_url(f"/claims/{claim_id}/events"), json=body, headers=_HEADERS, timeout=10)

    # Persist fraud columns on the claim for dashboard queries
    httpx.patch(
        _url(f"/claims/{claim_id}"),
        json={"fraud_risk_level": risk_level, "fraud_risk_score": score},
        headers=_HEADERS,
        timeout=10,
    )

    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Repair cost estimate
# ---------------------------------------------------------------------------
@tool
def estimate_repair_cost(
    claim_id: str,
    estimated_min: int,
    estimated_max: int,
    deductible: int,
    coverage_limit: int,
) -> str:
    """Record a repair cost estimate and calculate deductible/coverage payout.

    Call this AFTER the damage assessment (photo or description) and BEFORE
    informing the customer of the final decision. The LLM provides its own
    cost estimate in South African Rand (ZAR) based on the photo analysis,
    and this tool calculates the customer's out-of-pocket vs coverage payout.

    Args:
        claim_id: The UUID of the claim.
        estimated_min: Lower bound of the estimated repair cost in ZAR (e.g. 5000).
        estimated_max: Upper bound of the estimated repair cost in ZAR (e.g. 15000).
        deductible: The deductible amount from the policy coverage (in Rand).
        coverage_limit: The coverage limit from the policy (in Rand).
    """
    low = estimated_min
    high = estimated_max

    # Sanity: ensure low <= high
    if low > high:
        low, high = high, low

    mid_estimate = (low + high) // 2

    exceeds_limit = high > coverage_limit

    customer_pays = min(deductible, mid_estimate)
    coverage_pays = min(mid_estimate - customer_pays, coverage_limit)

    result = {
        "estimated_range": f"R{low:,} - R{high:,}",
        "mid_estimate": f"R{mid_estimate:,}",
        "customer_deductible": f"R{customer_pays:,}",
        "estimated_coverage_payout": f"R{coverage_pays:,}",
        "coverage_limit": f"R{coverage_limit:,}",
        "exceeds_limit": exceeds_limit,
    }

    # Log to audit trail
    body = {
        "event_type": "tool_result",
        "message": f"Repair cost estimate: {result['estimated_range']}.",
        "payload": result,
    }
    httpx.post(_url(f"/claims/{claim_id}/events"), json=body, headers=_HEADERS, timeout=10)

    # Persist cost estimate columns on the claim for dashboard queries
    httpx.patch(
        _url(f"/claims/{claim_id}"),
        json={"estimated_cost_min": float(low), "estimated_cost_max": float(high)},
        headers=_HEADERS,
        timeout=10,
    )

    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Policy upgrade recommendations
# ---------------------------------------------------------------------------
_UPGRADE_OPTIONS: dict[str, dict[str, Any]] = {
    # All amounts in South African Rand (ZAR)
    "collision": {
        "coverage_type": "collision",
        "name": "Collision Coverage",
        "description": "Covers damage to your vehicle from collisions with other vehicles or objects (poles, guardrails, etc.), regardless of fault.",
        "tiers": [
            {"tier": "Basic",    "deductible": 2500, "limit":  50000, "max_severity": "moderate", "monthly_premium": 580},
            {"tier": "Standard", "deductible": 1500, "limit": 100000, "max_severity": "severe",   "monthly_premium": 850},
            {"tier": "Premium",  "deductible":  750, "limit": 200000, "max_severity": "severe",   "monthly_premium": 1250},
        ],
    },
    "comprehensive": {
        "coverage_type": "comprehensive",
        "name": "Comprehensive Coverage",
        "description": "Covers non-collision events: theft, vandalism, weather damage (hail, flood, storm), fire, falling objects, and animal strikes.",
        "tiers": [
            {"tier": "Basic",    "deductible": 2000, "limit":  50000, "max_severity": "moderate", "monthly_premium": 420},
            {"tier": "Standard", "deductible": 1000, "limit": 100000, "max_severity": "severe",   "monthly_premium": 650},
            {"tier": "Premium",  "deductible":  500, "limit": 150000, "max_severity": "severe",   "monthly_premium": 950},
        ],
    },
    "roadside": {
        "coverage_type": "roadside",
        "name": "Roadside Assistance",
        "description": "24/7 roadside help including towing, flat tyre change, jump start, lockout service, and fuel delivery.",
        "tiers": [
            {"tier": "Basic",    "deductible": None, "limit": 2500, "max_severity": None, "monthly_premium": 110},
            {"tier": "Standard", "deductible": None, "limit": 5000, "max_severity": None, "monthly_premium": 180},
        ],
    },
    "glass": {
        "coverage_type": "glass",
        "name": "Glass Coverage",
        "description": "Covers windshield and window repair or replacement with no deductible on repairs.",
        "tiers": [
            {"tier": "Basic",    "deductible": 500, "limit":  8000, "max_severity": "moderate", "monthly_premium": 140},
            {"tier": "Standard", "deductible":   0, "limit": 15000, "max_severity": "severe",   "monthly_premium": 230},
        ],
    },
}


@tool
def get_upgrade_options(
    policy_number: str,
    recommended_coverage: Optional[str] = None,
) -> str:
    """Get available coverage upgrade options for a policy.

    Call this when a claim is DENIED because the policy lacks the required
    coverage (e.g. no collision or no comprehensive). It returns upgrade
    plans the customer could add to prevent future claim denials.

    Also useful if a customer proactively asks about improving their coverage.

    Args:
        policy_number: The policy number to look up current coverages for.
        recommended_coverage: Optional — the specific missing coverage type
                              to recommend (collision, comprehensive, roadside, glass).
                              If omitted, returns all coverages the policy is missing.
    """
    # Fetch current policy coverages
    resp = httpx.get(_url(f"/policies/{policy_number}"), headers=_HEADERS, timeout=10)
    if resp.status_code != 200:
        return _error(resp)

    policy = resp.json()
    existing_types = {c["coverage_type"] for c in policy.get("coverages", [])}

    # Determine which coverages to suggest
    if recommended_coverage:
        if recommended_coverage in existing_types:
            return json.dumps({
                "message": f"Policy {policy_number} already has {recommended_coverage} coverage.",
                "upgrades": [],
            })
        suggestions = [recommended_coverage]
    else:
        suggestions = [ct for ct in _UPGRADE_OPTIONS if ct not in existing_types]

    if not suggestions:
        return json.dumps({
            "message": f"Policy {policy_number} already has all available coverage types.",
            "upgrades": [],
        })

    upgrades = []
    for ctype in suggestions:
        option = _UPGRADE_OPTIONS.get(ctype)
        if option:
            upgrades.append(option)

    return json.dumps({
        "policy_number": policy_number,
        "current_coverages": sorted(existing_types),
        "recommended_upgrades": upgrades,
    }, indent=2)


# ---------------------------------------------------------------------------
# Claim report (PDF)
# ---------------------------------------------------------------------------
_REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def _pdf_safe(text: str) -> str:
    """Replace Unicode characters that Helvetica cannot render."""
    return (
        text
        .replace("\u2013", "-")   # en-dash
        .replace("\u2014", "-")   # em-dash
        .replace("\u2018", "'")   # left single quote
        .replace("\u2019", "'")   # right single quote
        .replace("\u201c", '"')   # left double quote
        .replace("\u201d", '"')   # right double quote
        .replace("\u2026", "...")  # ellipsis
        .replace("\u2022", "-")   # bullet
        .replace("\u2192", "->")  # rightwards arrow
    )


@tool
def generate_claim_report(claim_id: str, policy_number: str) -> str:
    """Generate a PDF claim report and save it to the reports/ folder.

    Call this at the END of the claim process, after the final decision
    has been made. It produces a professional summary PDF with all
    claim details, assessment findings, and the audit trail.

    Args:
        claim_id: The UUID of the claim.
        policy_number: The policy number associated with the claim.
    """
    from fpdf import FPDF

    # Fetch claim data
    claim_resp = httpx.get(_url(f"/claims/{claim_id}"), headers=_HEADERS, timeout=10)
    if claim_resp.status_code != 200:
        return _error(claim_resp)
    claim = claim_resp.json()

    # Fetch policy data
    policy_resp = httpx.get(_url(f"/policies/{policy_number}"), headers=_HEADERS, timeout=10)
    if policy_resp.status_code != 200:
        return _error(policy_resp)
    policy = policy_resp.json()

    # Create reports directory
    _REPORTS_DIR.mkdir(exist_ok=True)

    # Build PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Header ---
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Atlas Insurance", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Auto Claims Triage Report", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # --- Divider ---
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # --- Claim Details ---
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Claim Details", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)

    details = [
        ("Claim Number", claim.get("claim_number", "N/A")),
        ("Status", claim.get("status", "N/A").upper()),
        ("Incident Date", claim.get("incident_date", "N/A")),
        ("Incident Type", claim.get("incident_type", "N/A")),
        ("Decision", claim.get("decision_reason", "N/A")),
    ]
    for label, value in details:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(50, 6, f"{label}:")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, _pdf_safe(str(value)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Description
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Description:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _pdf_safe(claim.get("description", "N/A")))
    pdf.ln(4)

    # --- Policy Summary ---
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Policy Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)

    customer_name = policy.get("customer", {}).get("full_name", "N/A")
    policy_details = [
        ("Customer", customer_name),
        ("Policy Number", policy.get("policy_number", "N/A")),
        ("Status", policy.get("status", "N/A")),
        ("Period", f"{policy.get('start_date', 'N/A')} to {policy.get('end_date', 'N/A')}"),
    ]
    for label, value in policy_details:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(50, 6, f"{label}:")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, _pdf_safe(str(value)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Coverages table
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Coverages:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for cov in policy.get("coverages", []):
        ded = f"R{cov['deductible_amount']:,}" if cov.get("deductible_amount") else "N/A"
        lim = f"R{cov['limit_amount']:,}" if cov.get("limit_amount") else "N/A"
        sev = cov.get("max_severity") or "N/A"
        pdf.cell(0, 5, _pdf_safe(f"  - {cov['coverage_type'].title()}: deductible {ded}, limit {lim}, max severity {sev}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # --- Audit Trail ---
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Audit Trail", new_x="LMARGIN", new_y="NEXT")

    events = claim.get("events", [])
    if events:
        for event in events:
            pdf.set_font("Helvetica", "B", 9)
            ts = event.get("created_at", "")[:19].replace("T", " ")
            pdf.cell(0, 5, _pdf_safe(f"[{ts}] {event.get('event_type', 'note').upper()}"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 4, _pdf_safe(event.get("message", "")))
            pdf.ln(2)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, "No events recorded.", new_x="LMARGIN", new_y="NEXT")

    # Save
    claim_number = claim.get("claim_number", "unknown")
    filename = f"{claim_number}_report.pdf"
    filepath = _REPORTS_DIR / filename
    pdf.output(str(filepath))

    return json.dumps({
        "status": "success",
        "filename": filename,
        "path": str(filepath),
        "message": f"PDF report saved to reports/{filename}",
    })


# ---------------------------------------------------------------------------
# Email claim report to customer
# ---------------------------------------------------------------------------
_ALLOWED_RECIPIENT = "christiaanbecker9@icloud.com"


@tool
def send_claim_email(
    claim_id: str,
    policy_number: str,
) -> str:
    """Email the claim PDF report to the customer.

    Call this AFTER `generate_claim_report` has been called and the PDF exists.
    It sends the PDF as an attachment to the customer's email address.

    Args:
        claim_id: The UUID of the claim.
        policy_number: The policy number associated with the claim.
    """
    import resend

    resend.api_key = os.getenv("RESEND_API_KEY", "")
    if not resend.api_key:
        return json.dumps({"error": "RESEND_API_KEY not configured"})

    sender_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    # Fetch claim to get claim_number
    claim_resp = httpx.get(_url(f"/claims/{claim_id}"), headers=_HEADERS, timeout=10)
    if claim_resp.status_code != 200:
        return _error(claim_resp)
    claim = claim_resp.json()
    claim_number = claim.get("claim_number", "unknown")
    status = claim.get("status", "unknown").upper()

    # Fetch customer name from policy
    policy_resp = httpx.get(_url(f"/policies/{policy_number}"), headers=_HEADERS, timeout=10)
    customer_name = "Valued Customer"
    if policy_resp.status_code == 200:
        customer_name = policy_resp.json().get("customer", {}).get("full_name", customer_name)

    # Locate the PDF
    filename = f"{claim_number}_report.pdf"
    filepath = _REPORTS_DIR / filename
    if not filepath.exists():
        return json.dumps({"error": f"Report PDF not found at {filepath}. Call generate_claim_report first."})

    pdf_bytes = filepath.read_bytes()

    params: dict[str, Any] = {
        "from": sender_email,
        "to": [_ALLOWED_RECIPIENT],
        "subject": f"Atlas Insurance - Claim {claim_number} Report",
        "html": (
            f"<p>Dear {customer_name},</p>"
            f"<p>Please find attached the report for your claim <strong>{claim_number}</strong> "
            f"(status: <strong>{status}</strong>).</p>"
            f"<p>If you have any questions, please reply to this email or call us at "
            f"1-800-ATLAS-INS.</p>"
            f"<br><p>Kind regards,<br>Atlas Insurance Claims Team</p>"
        ),
        "attachments": [
            {
                "filename": filename,
                "content": list(pdf_bytes),
            }
        ],
    }

    try:
        email = resend.Emails.send(params)
        # Log to audit trail
        body = {
            "event_type": "note",
            "message": f"Claim report emailed to {_ALLOWED_RECIPIENT}.",
            "payload": {"email_id": email.get("id", "unknown"), "recipient": _ALLOWED_RECIPIENT},
        }
        httpx.post(_url(f"/claims/{claim_id}/events"), json=body, headers=_HEADERS, timeout=10)

        return json.dumps({
            "status": "sent",
            "email_id": email.get("id", "unknown"),
            "to": _ALLOWED_RECIPIENT,
            "claim_number": claim_number,
            "message": f"Claim report emailed to {_ALLOWED_RECIPIENT}",
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to send email: {str(e)}"})
