"""Seed the insurance database with demo data.

Run:  python seed.py  (requires DATABASE_URL env var or .env file)
"""

import asyncio
import uuid
from datetime import date, datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from app.database import async_session, engine
from app.models import Base, Claim, ClaimEvent, Coverage, Customer, Policy

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uuid() -> uuid.UUID:
    return uuid.uuid4()

def _now() -> datetime:
    return datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# Customers (10)
# ---------------------------------------------------------------------------
customers = [
    Customer(id=_uuid(), full_name="Alice Johnson", created_at=_now()),
    Customer(id=_uuid(), full_name="Bob Williams", created_at=_now()),
    Customer(id=_uuid(), full_name="Carol Martinez", created_at=_now()),
    Customer(id=_uuid(), full_name="David Brown", created_at=_now()),
    Customer(id=_uuid(), full_name="Emma Davis", created_at=_now()),
    Customer(id=_uuid(), full_name="Frank Wilson", created_at=_now()),
    Customer(id=_uuid(), full_name="Grace Lee", created_at=_now()),
    Customer(id=_uuid(), full_name="Henry Taylor", created_at=_now()),
    Customer(id=_uuid(), full_name="Irene Anderson", created_at=_now()),
    Customer(id=_uuid(), full_name="James Thomas", created_at=_now()),
]

# ---------------------------------------------------------------------------
# Policies (21) — 13 active, 4 lapsed, 4 cancelled
# ---------------------------------------------------------------------------
policies: list[Policy] = []
coverages: list[Coverage] = []

def _add_policy(
    customer: Customer,
    number: str,
    status: str,
    start: date,
    end: date,
    cov_types: list[tuple[str, int | None, int | None, str | None]],
):
    pid = _uuid()
    p = Policy(
        id=pid,
        customer_id=customer.id,
        policy_number=number,
        status=status,
        start_date=start,
        end_date=end,
        created_at=_now(),
    )
    policies.append(p)
    for ctype, ded, lim, sev in cov_types:
        coverages.append(
            Coverage(
                id=_uuid(),
                policy_id=pid,
                coverage_type=ctype,
                deductible_amount=ded,
                limit_amount=lim,
                max_severity=sev,
                created_at=_now(),
            )
        )

# -- Active policies (15) — limits in realistic South African Rand (ZAR) --

# 1. Alice: full coverage (collision + comprehensive + liability)
_add_policy(customers[0], "POL-ACTIVE-001", "active", date(2024, 1, 1), date(2026, 12, 31), [
    ("collision", 500, 150000, "severe"),
    ("comprehensive", 250, 150000, "severe"),
    ("liability", None, 100000, None),
])

# 2. Alice: second car — liability only (no collision!)
_add_policy(customers[0], "POL-ACTIVE-002", "active", date(2024, 6, 1), date(2026, 6, 1), [
    ("liability", None, 50000, None),
])

# 3. Bob: collision + liability
_add_policy(customers[1], "POL-ACTIVE-003", "active", date(2024, 3, 1), date(2026, 3, 1), [
    ("collision", 1000, 150000, "severe"),
    ("liability", None, 100000, None),
])

# 4. Carol: comprehensive + liability (no collision — good for theft/weather)
_add_policy(customers[2], "POL-ACTIVE-004", "active", date(2024, 2, 1), date(2026, 2, 1), [
    ("comprehensive", 500, 150000, "severe"),
    ("liability", None, 100000, None),
])

# 5. David: full coverage + roadside
_add_policy(customers[3], "POL-ACTIVE-005", "active", date(2024, 4, 1), date(2026, 4, 1), [
    ("collision", 500, 150000, "severe"),
    ("comprehensive", 250, 150000, "severe"),
    ("liability", None, 100000, None),
    ("roadside", None, 5000, None),
])

# 6. Emma: liability only
_add_policy(customers[4], "POL-ACTIVE-006", "active", date(2024, 5, 1), date(2026, 5, 1), [
    ("liability", None, 50000, None),
])

# 7. Frank: collision + comprehensive + liability
_add_policy(customers[5], "POL-ACTIVE-007", "active", date(2024, 1, 15), date(2026, 1, 15), [
    ("collision", 750, 150000, "severe"),
    ("comprehensive", 500, 150000, "severe"),
    ("liability", None, 100000, None),
])

# 8. Grace: comprehensive + liability (no collision)
_add_policy(customers[6], "POL-ACTIVE-008", "active", date(2024, 7, 1), date(2026, 7, 1), [
    ("comprehensive", 300, 150000, "severe"),
    ("liability", None, 75000, None),
])

# 9. Henry: collision + liability
_add_policy(customers[7], "POL-ACTIVE-009", "active", date(2024, 8, 1), date(2026, 8, 1), [
    ("collision", 500, 150000, "severe"),
    ("liability", None, 100000, None),
])

# 10. Irene: full coverage
_add_policy(customers[8], "POL-ACTIVE-010", "active", date(2024, 9, 1), date(2026, 9, 1), [
    ("collision", 500, 150000, "severe"),
    ("comprehensive", 250, 150000, "severe"),
    ("liability", None, 100000, None),
])

# 11. James: comprehensive only + liability
_add_policy(customers[9], "POL-ACTIVE-011", "active", date(2024, 10, 1), date(2026, 10, 1), [
    ("comprehensive", 500, 150000, "severe"),
    ("liability", None, 50000, None),
])

# 12. Bob second car: collision + comprehensive + liability
_add_policy(customers[1], "POL-ACTIVE-012", "active", date(2024, 11, 1), date(2026, 11, 1), [
    ("collision", 500, 150000, "severe"),
    ("comprehensive", 250, 150000, "severe"),
    ("liability", None, 100000, None),
])

# 13. Frank second car: budget collision (minor damage only — intentionally low limit for demo)
_add_policy(customers[5], "POL-ACTIVE-013", "active", date(2024, 1, 1), date(2026, 12, 31), [
    ("collision", 500, 8000, "minor"),
    ("liability", None, 50000, None),
])

# 14. Grace: brand-new policy (started Feb 2026 — fraud demo: NEW_POLICY flag)
_add_policy(customers[6], "POL-ACTIVE-014", "active", date(2026, 2, 1), date(2028, 2, 1), [
    ("collision", 500, 150000, "severe"),
    ("comprehensive", 250, 150000, "severe"),
    ("liability", None, 100000, None),
])

# 15. Henry: low-limit collision (intentionally low — demo: estimate exceeds limit → escalate)
_add_policy(customers[7], "POL-ACTIVE-015", "active", date(2024, 8, 1), date(2026, 8, 1), [
    ("collision", 500, 30000, "severe"),
    ("liability", None, 100000, None),
])

# -- Lapsed policies (4) --

_add_policy(customers[2], "POL-LAPSED-001", "lapsed", date(2023, 1, 1), date(2025, 1, 1), [
    ("collision", 500, 150000, "severe"),
    ("comprehensive", 250, 150000, "severe"),
    ("liability", None, 100000, None),
])

_add_policy(customers[3], "POL-LAPSED-002", "lapsed", date(2023, 6, 1), date(2025, 6, 1), [
    ("collision", 1000, 150000, "severe"),
    ("liability", None, 50000, None),
])

_add_policy(customers[5], "POL-LAPSED-003", "lapsed", date(2023, 3, 1), date(2025, 3, 1), [
    ("comprehensive", 500, 150000, "severe"),
    ("liability", None, 100000, None),
])

_add_policy(customers[7], "POL-LAPSED-004", "lapsed", date(2023, 9, 1), date(2025, 9, 1), [
    ("collision", 500, 150000, "severe"),
    ("liability", None, 100000, None),
])

# -- Cancelled policies (4) --

_add_policy(customers[4], "POL-CANCEL-001", "cancelled", date(2023, 2, 1), date(2024, 2, 1), [
    ("collision", 500, 150000, "severe"),
    ("comprehensive", 250, 150000, "severe"),
    ("liability", None, 100000, None),
])

_add_policy(customers[6], "POL-CANCEL-002", "cancelled", date(2023, 5, 1), date(2024, 5, 1), [
    ("liability", None, 50000, None),
])

_add_policy(customers[8], "POL-CANCEL-003", "cancelled", date(2023, 8, 1), date(2024, 8, 1), [
    ("collision", 750, 150000, "severe"),
    ("liability", None, 100000, None),
])

_add_policy(customers[9], "POL-CANCEL-004", "cancelled", date(2023, 11, 1), date(2024, 11, 1), [
    ("comprehensive", 500, 150000, "severe"),
    ("liability", None, 50000, None),
])


# ---------------------------------------------------------------------------
# Main seed routine
# ---------------------------------------------------------------------------
async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Pre-existing claims (for fraud demo — repeat claimant on POL-ACTIVE-007)
    existing_claims = []
    pol_007 = next(p for p in policies if p.policy_number == "POL-ACTIVE-007")
    existing_claims.append(Claim(
        id=_uuid(),
        claim_number="CLM-PRIOR-001",
        policy_id=pol_007.id,
        status="accepted",
        description="Rear-ended at traffic light, bumper damage.",
        incident_date=date(2025, 3, 15),
        incident_type="collision",
        decision_reason="Policy active, collision coverage verified.",
        created_at=_now(),
        updated_at=_now(),
    ))
    existing_claims.append(Claim(
        id=_uuid(),
        claim_number="CLM-PRIOR-002",
        policy_id=pol_007.id,
        status="accepted",
        description="Hail damage to roof and hood.",
        incident_date=date(2025, 8, 20),
        incident_type="weather",
        decision_reason="Policy active, comprehensive coverage verified.",
        created_at=_now(),
        updated_at=_now(),
    ))

    async with async_session() as session:
        session.add_all(customers)
        await session.flush()
        session.add_all(policies)
        await session.flush()
        session.add_all(coverages)
        await session.flush()
        session.add_all(existing_claims)
        await session.commit()

    print(f"Seeded {len(customers)} customers, {len(policies)} policies, {len(coverages)} coverages.")
    print()
    print("=== Demo policy numbers ===")
    print("Scenario 1 (accepted collision):         POL-ACTIVE-001  (Alice, full coverage, severity: severe)")
    print("Scenario 2 (denied, no collision cov):   POL-ACTIVE-002  (Alice, liability only)")
    print("Scenario 3 (denied, policy lapsed):      POL-LAPSED-001  (Carol, lapsed)")
    print("Scenario 4 (needs info / vague):         POL-ACTIVE-004  (Carol, comprehensive + liability)")
    print("Scenario 5 (escalated, severity exceed): POL-ACTIVE-013  (Frank, budget collision, severity: minor only)")
    print("Scenario 6 (fraud - new policy):         POL-ACTIVE-014  (Grace, brand-new policy started Feb 2026)")
    print("Scenario 7 (fraud - repeat claimant):    POL-ACTIVE-007  (Frank, 2 prior claims on record)")
    print("Scenario 8 (escalated, limit exceed):    POL-ACTIVE-015  (Henry, collision limit $3,000; severity allowed)")
    print()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
