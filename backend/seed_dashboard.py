"""Seed the database with 75 realistic claims for the dashboard demo.

Usage:
    cd backend && python seed_dashboard.py

Idempotent: skips if CLM-DASH-001 already exists.
"""

import asyncio
import random
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, engine
from app.models import Base, Claim, ClaimEvent, Customer, Policy

random.seed(42)

NUM_CLAIMS = 75


def _now():
    return datetime.now(timezone.utc)


def _rand_ts(base: datetime, offset_hours_range: tuple[float, float]) -> datetime:
    lo, hi = offset_hours_range
    return base + timedelta(hours=random.uniform(lo, hi))


# Descriptions per incident type
_DESCRIPTIONS = {
    "collision": [
        "Rear-ended at a red light on Jan Smuts Avenue. Bumper and taillight damaged.",
        "Side collision at a four-way stop. Driver door dented and side mirror broken.",
        "Hit a pothole on the N1, causing front axle damage and flat tyre.",
        "T-bone collision at William Nicol intersection. Significant passenger side damage.",
        "Reversed into a concrete bollard in parking garage. Rear bumper cracked.",
        "Multi-vehicle pile-up on the M1 during rush hour. Front fender crushed.",
        "Clipped by a taxi on Commissioner Street. Paint scratched and panel dented.",
        "Head-on collision on gravel road in Limpopo. Radiator and bonnet damaged.",
    ],
    "theft": [
        "Vehicle stolen from driveway in Sandton overnight. No signs of forced entry.",
        "Smash-and-grab at a traffic light in Hillbrow. Window broken, laptop bag stolen.",
        "Side mirrors and wheels stolen while parked at mall in Centurion.",
        "Vehicle hijacked at gunpoint near Berea. Recovered 3 days later, stripped.",
    ],
    "weather": [
        "Severe hailstorm in Johannesburg. Roof and bonnet covered in dents.",
        "Flash flooding in Durban caused water damage to engine and interior.",
        "Tree branch fell on vehicle during storm in Cape Town. Windshield shattered.",
        "Lightning strike near parked vehicle caused electrical system failure.",
    ],
    "glass": [
        "Stone chip on the N3 highway cracked windshield across full width.",
        "Rear window shattered by unknown projectile while parked in Soweto.",
        "Side window cracked from thermal stress during heatwave.",
    ],
}

_DECISION_REASONS = {
    "accepted": [
        "Policy active, coverage verified. Incident consistent with claim type.",
        "All documentation provided. Coverage confirmed, within policy limits.",
        "Fraud check passed. Damage assessment consistent with description.",
        "Straight-through processing. Low risk, valid coverage.",
    ],
    "denied": [
        "Policy lapsed at time of incident. No active coverage.",
        "Incident type not covered under current policy coverages.",
        "Damage severity exceeds policy max_severity limit.",
        "Claim filed outside the 30-day reporting window.",
    ],
    "escalated": [
        "High fraud risk score. Requires manual investigation.",
        "Conflicting witness statements. Needs further review.",
        "Damage assessment inconsistent with customer description.",
        "Multiple claims in short period. Senior adjuster review required.",
    ],
}


async def seed(db: AsyncSession):
    # Check idempotency
    existing = await db.execute(select(Claim).where(Claim.claim_number == "CLM-DASH-001"))
    if existing.scalar_one_or_none():
        print("Dashboard claims already seeded (CLM-DASH-001 exists). Skipping.")
        return

    # Load all policies with their customers
    policies_result = await db.execute(
        select(Policy).where(Policy.status == "active")
    )
    active_policies = list(policies_result.scalars().all())
    if not active_policies:
        print("No active policies found. Run the app first to seed base data.")
        return

    now = _now()
    claims = []
    events = []

    # Status distribution
    statuses = (
        ["accepted"] * 45
        + ["denied"] * 11
        + ["escalated"] * 8
        + ["needs_info"] * 7
        + ["intake"] * 4
    )
    random.shuffle(statuses)

    # Type distribution
    types = (
        ["collision"] * 38
        + ["theft"] * 12
        + ["weather"] * 10
        + ["glass"] * 8
        + ["unknown"] * 7
    )
    random.shuffle(types)

    for i in range(NUM_CLAIMS):
        claim_num = f"CLM-DASH-{i + 1:03d}"
        status = statuses[i]
        inc_type = types[i]
        policy = random.choice(active_policies)

        # Spread claims across last 30 days (triangular distribution — more recent)
        days_ago = int(random.triangular(0, 30, 5))
        created_at = now - timedelta(days=days_ago, hours=random.uniform(0, 23), minutes=random.randint(0, 59))
        incident_date = (created_at - timedelta(days=random.randint(0, 3))).date()

        # Processing time in SECONDS — realistic for an AI agent
        if status == "accepted":
            secs_to_resolve = random.uniform(15, 90)       # STP auto-approve
        elif status == "denied":
            secs_to_resolve = random.uniform(30, 120)      # policy check → deny
        elif status == "escalated":
            secs_to_resolve = random.uniform(45, 180)      # fraud flag → escalate
        elif status == "needs_info":
            secs_to_resolve = random.uniform(20, 60)       # quick triage
        else:  # intake
            secs_to_resolve = random.uniform(5, 30)        # just received

        updated_at = created_at + timedelta(seconds=secs_to_resolve)

        # Fraud risk
        fraud_roll = random.random()
        if fraud_roll < 0.12:
            fraud_level, fraud_score = "high", random.randint(50, 95)
        elif fraud_roll < 0.32:
            fraud_level, fraud_score = "medium", random.randint(25, 49)
        else:
            fraud_level, fraud_score = "low", random.randint(0, 24)

        # Cost estimate
        if inc_type in _DESCRIPTIONS and inc_type != "unknown":
            desc_choices = _DESCRIPTIONS[inc_type]
        else:
            desc_choices = _DESCRIPTIONS["collision"]
        description = random.choice(desc_choices)

        # Cost ranges by type — realistic South African Rand (ZAR) amounts
        cost_ranges = {
            "collision": (2_500,  90_000),
            "theft":     (2_000, 160_000),
            "weather":   (2_000,  80_000),
            "glass":     (500,    10_000),
            "unknown":   (2_000,  60_000),
        }
        lo, hi = cost_ranges.get(inc_type, (500, 8000))
        cost_min = round(random.uniform(lo * 0.5, lo * 1.5), 2)
        cost_max = round(random.uniform(hi * 0.7, hi * 1.3), 2)
        if cost_max < cost_min:
            cost_min, cost_max = cost_max, cost_min

        # Decision reason (only for decided claims)
        decision_reason = None
        if status in _DECISION_REASONS:
            decision_reason = random.choice(_DECISION_REASONS[status])

        claim_id = uuid.uuid4()
        claims.append(Claim(
            id=claim_id,
            claim_number=claim_num,
            policy_id=policy.id,
            status=status,
            incident_date=incident_date,
            incident_type=inc_type if inc_type != "unknown" else None,
            description=description,
            decision_reason=decision_reason,
            fraud_risk_level=fraud_level,
            fraud_risk_score=fraud_score,
            estimated_cost_min=cost_min,
            estimated_cost_max=cost_max,
            created_at=created_at,
            updated_at=updated_at,
        ))

        # Generate 3-5 events per claim
        event_time = created_at + timedelta(minutes=random.randint(1, 10))

        # Event 1: intake note
        events.append(ClaimEvent(
            id=uuid.uuid4(),
            claim_id=claim_id,
            event_type="note",
            message="Claim created via FNOL intake.",
            payload={"source": "api"},
            created_at=event_time,
        ))

        # Event 2: fraud check
        event_time += timedelta(minutes=random.randint(5, 30))
        events.append(ClaimEvent(
            id=uuid.uuid4(),
            claim_id=claim_id,
            event_type="tool_result",
            message=f"Fraud check: risk_level={fraud_level}, score={fraud_score}/100.",
            payload={"risk_score": fraud_score, "risk_level": fraud_level, "flags": []},
            created_at=event_time,
        ))

        # Event 3: cost estimate
        event_time += timedelta(minutes=random.randint(5, 20))
        events.append(ClaimEvent(
            id=uuid.uuid4(),
            claim_id=claim_id,
            event_type="tool_result",
            message=f"Repair cost estimate: R{cost_min:,.0f} - R{cost_max:,.0f}.",
            payload={"estimated_cost_min": cost_min, "estimated_cost_max": cost_max},
            created_at=event_time,
        ))

        # Event 4: decision (for decided claims)
        if status in ("accepted", "denied", "escalated"):
            event_time += timedelta(minutes=random.randint(10, 60))
            events.append(ClaimEvent(
                id=uuid.uuid4(),
                claim_id=claim_id,
                event_type="decision",
                message=decision_reason or f"Claim {status}.",
                payload={"status": status},
                created_at=event_time,
            ))

        # Event 5: status change
        if status != "intake":
            event_time += timedelta(minutes=random.randint(1, 5))
            events.append(ClaimEvent(
                id=uuid.uuid4(),
                claim_id=claim_id,
                event_type="status_change",
                message=f"Status changed from 'intake' to '{status}'.",
                payload={"old_status": "intake", "new_status": status},
                created_at=event_time,
            ))

    db.add_all(claims)
    await db.flush()
    db.add_all(events)
    await db.commit()
    print(f"Seeded {len(claims)} dashboard claims and {len(events)} events.")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
