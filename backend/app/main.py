import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import API_KEY
from app.database import engine, get_db
from app.models import Base, Claim, ClaimEvent, Coverage, Customer, Policy, City, RepairShop
from app.schemas import (
    ClaimCreate,
    ClaimCreateResponse,
    ClaimEventCreate,
    ClaimEventOut,
    ClaimOut,
    ClaimPatch,
    ClaimSummaryOut,
    DashboardResponse,
    PolicyOut,
    RepairShopOut,
)

app = FastAPI(title="Mock Insurance Core API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ---------------------------------------------------------------------------
# Startup: create tables
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.database import async_session
    # Seed demo customers, policies, coverages (idempotent)
    async with async_session() as db:
        await _seed_demo_data(db)
    # Seed reference data for South African cities and approved repair shops (idempotent)
    async with async_session() as db:
        await _seed_cities_and_shops(db)


async def _seed_demo_data(db: AsyncSession):
    """Seed customers, policies, coverages, and prior claims if DB is empty."""
    existing = await db.execute(select(Customer))
    if existing.scalars().first():
        return  # already seeded

    _uid = uuid.uuid4
    _now = lambda: datetime.now(timezone.utc)

    # --- 10 Customers ---
    customers = [
        Customer(id=_uid(), full_name="Alice Johnson", created_at=_now()),
        Customer(id=_uid(), full_name="Bob Williams", created_at=_now()),
        Customer(id=_uid(), full_name="Carol Martinez", created_at=_now()),
        Customer(id=_uid(), full_name="David Brown", created_at=_now()),
        Customer(id=_uid(), full_name="Emma Davis", created_at=_now()),
        Customer(id=_uid(), full_name="Frank Wilson", created_at=_now()),
        Customer(id=_uid(), full_name="Grace Lee", created_at=_now()),
        Customer(id=_uid(), full_name="Henry Taylor", created_at=_now()),
        Customer(id=_uid(), full_name="Irene Anderson", created_at=_now()),
        Customer(id=_uid(), full_name="James Thomas", created_at=_now()),
    ]
    db.add_all(customers)
    await db.flush()

    # --- Helper to build policy + coverages ---
    policies = []
    coverages = []

    def _add_policy(customer, number, status, start, end, cov_types):
        pid = _uid()
        policies.append(Policy(
            id=pid, customer_id=customer.id, policy_number=number,
            status=status, start_date=start, end_date=end, created_at=_now(),
        ))
        for ctype, ded, lim, sev in cov_types:
            coverages.append(Coverage(
                id=_uid(), policy_id=pid, coverage_type=ctype,
                deductible_amount=ded, limit_amount=lim, max_severity=sev,
                created_at=_now(),
            ))

    # -- Active policies (13) --
    _add_policy(customers[0], "POL-ACTIVE-001", "active", date(2024, 1, 1), date(2026, 12, 31), [
        ("collision", 500, 150000, "severe"), ("comprehensive", 250, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[0], "POL-ACTIVE-002", "active", date(2024, 6, 1), date(2026, 6, 1), [
        ("liability", None, 50000, None),
    ])
    _add_policy(customers[1], "POL-ACTIVE-003", "active", date(2024, 3, 1), date(2026, 3, 1), [
        ("collision", 1000, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[2], "POL-ACTIVE-004", "active", date(2024, 2, 1), date(2026, 2, 1), [
        ("comprehensive", 500, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[3], "POL-ACTIVE-005", "active", date(2024, 4, 1), date(2026, 4, 1), [
        ("collision", 500, 150000, "severe"), ("comprehensive", 250, 150000, "severe"),
        ("liability", None, 100000, None), ("roadside", None, 500, None),
    ])
    _add_policy(customers[4], "POL-ACTIVE-006", "active", date(2024, 5, 1), date(2026, 5, 1), [
        ("collision", 750, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[5], "POL-ACTIVE-007", "active", date(2024, 7, 1), date(2026, 7, 1), [
        ("collision", 500, 150000, "severe"), ("comprehensive", 250, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[1], "POL-ACTIVE-008", "active", date(2024, 8, 1), date(2026, 8, 1), [
        ("comprehensive", 250, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[3], "POL-ACTIVE-009", "active", date(2024, 9, 1), date(2026, 9, 1), [
        ("collision", 500, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[4], "POL-ACTIVE-010", "active", date(2024, 10, 1), date(2026, 10, 1), [
        ("comprehensive", 500, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[8], "POL-ACTIVE-011", "active", date(2024, 11, 1), date(2026, 11, 1), [
        ("collision", 500, 150000, "severe"), ("comprehensive", 250, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[9], "POL-ACTIVE-012", "active", date(2024, 12, 1), date(2026, 12, 1), [
        ("comprehensive", 250, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[5], "POL-ACTIVE-013", "active", date(2024, 1, 1), date(2026, 12, 31), [
        ("collision", 500, 8000, "minor"), ("liability", None, 50000, None),  # intentionally low — budget/minor only
    ])
    _add_policy(customers[6], "POL-ACTIVE-014", "active", date(2026, 2, 1), date(2028, 2, 1), [
        ("collision", 500, 150000, "severe"), ("comprehensive", 250, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[7], "POL-ACTIVE-015", "active", date(2024, 8, 1), date(2026, 8, 1), [
        ("collision", 500, 30000, "severe"), ("liability", None, 100000, None),  # intentionally low — escalation demo
    ])

    # -- Lapsed policies (4) --
    _add_policy(customers[2], "POL-LAPSED-001", "lapsed", date(2023, 1, 1), date(2025, 1, 1), [
        ("collision", 500, 150000, "severe"), ("comprehensive", 250, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[3], "POL-LAPSED-002", "lapsed", date(2023, 6, 1), date(2025, 6, 1), [
        ("collision", 1000, 150000, "severe"), ("liability", None, 50000, None),
    ])
    _add_policy(customers[5], "POL-LAPSED-003", "lapsed", date(2023, 3, 1), date(2025, 3, 1), [
        ("comprehensive", 500, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[7], "POL-LAPSED-004", "lapsed", date(2023, 9, 1), date(2025, 9, 1), [
        ("collision", 500, 150000, "severe"), ("liability", None, 100000, None),
    ])

    # -- Cancelled policies (4) --
    _add_policy(customers[4], "POL-CANCEL-001", "cancelled", date(2023, 2, 1), date(2024, 2, 1), [
        ("collision", 500, 150000, "severe"), ("comprehensive", 250, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[6], "POL-CANCEL-002", "cancelled", date(2023, 5, 1), date(2024, 5, 1), [
        ("liability", None, 50000, None),
    ])
    _add_policy(customers[8], "POL-CANCEL-003", "cancelled", date(2023, 8, 1), date(2024, 8, 1), [
        ("collision", 750, 150000, "severe"), ("liability", None, 100000, None),
    ])
    _add_policy(customers[9], "POL-CANCEL-004", "cancelled", date(2023, 11, 1), date(2024, 11, 1), [
        ("comprehensive", 500, 150000, "severe"), ("liability", None, 50000, None),
    ])

    db.add_all(policies)
    await db.flush()
    db.add_all(coverages)
    await db.flush()

    # -- Prior claims for fraud demo (POL-ACTIVE-007 = Frank Wilson) --
    pol_007 = next(p for p in policies if p.policy_number == "POL-ACTIVE-007")
    prior_claims = [
        Claim(
            id=_uid(), claim_number="CLM-PRIOR-001", policy_id=pol_007.id,
            status="accepted", description="Rear-ended at traffic light, bumper damage.",
            incident_date=date(2025, 3, 15), incident_type="collision",
            decision_reason="Policy active, collision coverage verified.",
            created_at=_now(), updated_at=_now(),
        ),
        Claim(
            id=_uid(), claim_number="CLM-PRIOR-002", policy_id=pol_007.id,
            status="accepted", description="Hail damage to roof and hood.",
            incident_date=date(2025, 8, 20), incident_type="weather",
            decision_reason="Policy active, comprehensive coverage verified.",
            created_at=_now(), updated_at=_now(),
        ),
    ]
    db.add_all(prior_claims)
    await db.commit()
    print(f"Seeded {len(customers)} customers, {len(policies)} policies, {len(coverages)} coverages.")


async def _seed_cities_and_shops(db: AsyncSession):
    # Seed a small set of cities if they don't exist
    sa_cities = [
        ("Johannesburg", "Gauteng"),
        ("Cape Town", "Western Cape"),
        ("Durban", "KwaZulu-Natal"),
        ("Pretoria", "Gauteng"),
        ("Gqeberha", "Eastern Cape"),
    ]

    # Load existing names
    existing = await db.execute(select(City))
    existing_names = {c.name for c in existing.scalars().all()}

    city_objs: dict[str, City] = {}
    for name, province in sa_cities:
        if name in existing_names:
            # fetch the city object
            res = await db.execute(select(City).where(City.name == name))
            city_objs[name] = res.scalar_one()
        else:
            city = City(name=name, province=province)
            db.add(city)
            await db.flush()
            city_objs[name] = city

    # Seed 3–4 approved shops per city if none exist for that city
    for city_name, city in city_objs.items():
        res = await db.execute(select(RepairShop).where(RepairShop.city_id == city.id))
        if res.scalars().first():
            continue

        demo_shops = [
            {
                "name": f"{city_name} AutoCare",
                "address": f"101 Main Rd, {city_name}",
                "phone": "+27 10 555 0101",
                "email": "contact@autocare.co.za",
                "rating": 5,
            },
            {
                "name": f"{city_name} Panel & Paint",
                "address": f"22 Workshop St, {city_name}",
                "phone": "+27 10 555 0222",
                "email": "jobs@panelpaint.co.za",
                "rating": 4,
            },
            {
                "name": f"{city_name} QuickFix Motors",
                "address": f"7 Industrial Ave, {city_name}",
                "phone": "+27 10 555 0333",
                "email": None,
                "rating": 4,
            },
            {
                "name": f"{city_name} Elite Auto Works",
                "address": f"55 Service Ln, {city_name}",
                "phone": "+27 10 555 0444",
                "email": "hello@eliteautoworks.co.za",
                "rating": 5,
            },
        ]

        for shop in demo_shops:
            db.add(
                RepairShop(
                    city_id=city.id,
                    name=shop["name"],
                    address=shop["address"],
                    phone=shop["phone"],
                    email=shop["email"],
                    rating=shop["rating"],
                    approved=True,
                )
            )
    await db.commit()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------
@app.get("/policies/{policy_number}", response_model=PolicyOut, dependencies=[Depends(verify_api_key)])
async def get_policy(policy_number: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Policy)
        .where(Policy.policy_number == policy_number)
        .options(
            selectinload(Policy.customer),
            selectinload(Policy.coverages),
        )
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@app.get("/policies/{policy_number}/claims", response_model=list[ClaimSummaryOut], dependencies=[Depends(verify_api_key)])
async def get_policy_claims(policy_number: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Policy).where(Policy.policy_number == policy_number)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    stmt = select(Claim).where(Claim.policy_id == policy.id).order_by(Claim.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------
def _generate_claim_number() -> str:
    return f"CLM-{uuid.uuid4().hex[:8].upper()}"


@app.post("/claims", response_model=ClaimCreateResponse, dependencies=[Depends(verify_api_key)])
async def create_claim(body: ClaimCreate, db: AsyncSession = Depends(get_db)):
    # Lookup policy by number
    stmt = select(Policy).where(Policy.policy_number == body.policy_number)
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    claim = Claim(
        claim_number=_generate_claim_number(),
        policy_id=policy.id,
        status="intake",
        description=body.description,
        incident_date=body.incident_date,
        incident_type=body.incident_type,
    )
    db.add(claim)
    await db.flush()

    # Auto-create an intake event
    intake_event = ClaimEvent(
        claim_id=claim.id,
        event_type="note",
        message="Claim created via FNOL intake.",
        payload={"source": "api"},
    )
    db.add(intake_event)
    await db.commit()
    await db.refresh(claim)
    return claim


@app.get("/claims/{claim_id}", response_model=ClaimOut, dependencies=[Depends(verify_api_key)])
async def get_claim(claim_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Claim)
        .where(Claim.id == claim_id)
        .options(selectinload(Claim.events))
    )
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


# ---------------------------------------------------------------------------
# Recommendations: repair shops for accepted claims (by customer city)
# ---------------------------------------------------------------------------
@app.get(
    "/claims/{claim_id}/recommended-shops",
    response_model=list[RepairShopOut],
    dependencies=[Depends(verify_api_key)],
)
async def get_recommended_shops(claim_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Load claim with policy -> customer -> city
    stmt = (
        select(Claim)
        .where(Claim.id == claim_id)
        .options(
            selectinload(Claim.policy).selectinload(Policy.customer).selectinload(Customer.city),
        )
    )
    result = await db.execute(stmt)
    claim: Claim | None = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status != "accepted":
        raise HTTPException(status_code=400, detail="Recommendations available only for accepted claims")

    customer_city = claim.policy.customer.city if claim.policy and claim.policy.customer else None
    if not customer_city:
        raise HTTPException(status_code=400, detail="Customer city is not set; cannot recommend repair shops")

    shops_q = (
        select(RepairShop)
        .where(RepairShop.city_id == customer_city.id, RepairShop.approved == True)  # noqa: E712
        .order_by(RepairShop.rating.desc(), RepairShop.created_at.asc())
    )
    shops_res = await db.execute(shops_q)
    shops = shops_res.scalars().all()
    # Return top 4
    return shops[:4]


# ---------------------------------------------------------------------------
# Customers: set city (helper for demo)
# ---------------------------------------------------------------------------
@app.patch("/customers/{customer_id}/city", dependencies=[Depends(verify_api_key)])
async def set_customer_city(customer_id: uuid.UUID, city_name: str, db: AsyncSession = Depends(get_db)):
    # Find customer
    cust_res = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = cust_res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Find city by name (case-insensitive)
    city_res = await db.execute(select(City).where(City.name.ilike(city_name)))
    city = city_res.scalar_one_or_none()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    customer.city_id = city.id
    await db.commit()
    return {"customer_id": str(customer.id), "city": {"id": str(city.id), "name": city.name, "province": city.province}}


@app.patch("/claims/{claim_id}", response_model=ClaimOut, dependencies=[Depends(verify_api_key)])
async def update_claim(claim_id: uuid.UUID, body: ClaimPatch, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Claim)
        .where(Claim.id == claim_id)
        .options(selectinload(Claim.events))
    )
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    patch_data = body.model_dump(exclude_unset=True)

    old_status = claim.status
    for field, value in patch_data.items():
        setattr(claim, field, value)
    claim.updated_at = datetime.now(timezone.utc)

    # Auto-log status change
    if "status" in patch_data and patch_data["status"] != old_status:
        status_event = ClaimEvent(
            claim_id=claim.id,
            event_type="status_change",
            message=f"Status changed from '{old_status}' to '{patch_data['status']}'.",
            payload={"old_status": old_status, "new_status": patch_data["status"]},
        )
        db.add(status_event)

    await db.commit()
    await db.refresh(claim)
    return claim


# ---------------------------------------------------------------------------
# Audit events
# ---------------------------------------------------------------------------
@app.post("/claims/{claim_id}/events", response_model=ClaimEventOut, dependencies=[Depends(verify_api_key)])
async def create_claim_event(claim_id: uuid.UUID, body: ClaimEventCreate, db: AsyncSession = Depends(get_db)):
    # Verify claim exists
    stmt = select(Claim).where(Claim.id == claim_id)
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    event = ClaimEvent(
        claim_id=claim_id,
        event_type=body.event_type,
        message=body.message,
        payload=body.payload or {},
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.get("/dashboard", response_model=DashboardResponse, dependencies=[Depends(verify_api_key)])
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    # All claims in last 30 days
    stmt = select(Claim).where(Claim.created_at >= thirty_days_ago)
    result = await db.execute(stmt)
    claims = list(result.scalars().all())

    total = len(claims)

    # STP rate: accepted / (accepted + denied + escalated)
    decided = [c for c in claims if c.status in ("accepted", "denied", "escalated")]
    accepted = sum(1 for c in decided if c.status == "accepted")
    stp_rate = (accepted / len(decided) * 100) if decided else 0.0

    # Avg processing seconds (AI agent processes claims in seconds, not hours)
    processing_secs = []
    for c in claims:
        if c.updated_at and c.created_at:
            delta = (c.updated_at - c.created_at).total_seconds()
            processing_secs.append(delta)
    avg_secs = sum(processing_secs) / len(processing_secs) if processing_secs else 0.0

    # Fraud counts
    fraud_high = sum(1 for c in claims if c.fraud_risk_level == "high")
    fraud_medium = sum(1 for c in claims if c.fraud_risk_level == "medium")
    fraud_low = sum(1 for c in claims if c.fraud_risk_level == "low")

    # Avg repair cost
    costs = []
    for c in claims:
        if c.estimated_cost_min is not None and c.estimated_cost_max is not None:
            costs.append((c.estimated_cost_min + c.estimated_cost_max) / 2)
    avg_repair = sum(costs) / len(costs) if costs else 0.0

    # Claims by status
    status_counts: dict[str, int] = defaultdict(int)
    for c in claims:
        status_counts[c.status] += 1
    claims_by_status = [{"status": s, "count": n} for s, n in sorted(status_counts.items())]

    # Claims by type
    type_counts: dict[str, int] = defaultdict(int)
    for c in claims:
        type_counts[c.incident_type or "unknown"] += 1
    claims_by_type = [{"incident_type": t, "count": n} for t, n in sorted(type_counts.items())]

    # Claims trend (daily, last 30 days)
    trend: dict[str, dict[str, int]] = {}
    for i in range(30):
        d = (now - timedelta(days=29 - i)).strftime("%Y-%m-%d")
        trend[d] = {"accepted": 0, "denied": 0, "escalated": 0, "needs_info": 0, "intake": 0}
    for c in claims:
        d = c.created_at.strftime("%Y-%m-%d")
        if d in trend:
            trend[d][c.status] = trend[d].get(c.status, 0) + 1
    claims_trend = [{"date": d, **v} for d, v in trend.items()]

    # Fraud distribution
    fraud_distribution = [
        {"level": "high", "count": fraud_high},
        {"level": "medium", "count": fraud_medium},
        {"level": "low", "count": fraud_low},
    ]

    # Processing time buckets (in seconds — AI agent speed)
    buckets = {"<30s": 0, "30-60s": 0, "1-2m": 0, "2-3m": 0, ">3m": 0}
    for s in processing_secs:
        if s < 30:
            buckets["<30s"] += 1
        elif s < 60:
            buckets["30-60s"] += 1
        elif s < 120:
            buckets["1-2m"] += 1
        elif s < 180:
            buckets["2-3m"] += 1
        else:
            buckets[">3m"] += 1
    processing_time_buckets = [{"bucket": b, "count": n} for b, n in buckets.items()]

    # Recent claims (last 10) with customer name via join
    recent_stmt = (
        select(Claim, Customer.full_name)
        .join(Policy, Claim.policy_id == Policy.id)
        .join(Customer, Policy.customer_id == Customer.id)
        .order_by(Claim.created_at.desc())
        .limit(10)
    )
    recent_result = await db.execute(recent_stmt)
    recent_claims = []
    for claim, name in recent_result.all():
        mid = None
        if claim.estimated_cost_min is not None and claim.estimated_cost_max is not None:
            mid = (claim.estimated_cost_min + claim.estimated_cost_max) / 2
        recent_claims.append({
            "id": claim.id,
            "claim_number": claim.claim_number,
            "status": claim.status,
            "incident_type": claim.incident_type,
            "customer_name": name,
            "fraud_risk_level": claim.fraud_risk_level,
            "estimated_cost_mid": mid,
            "created_at": claim.created_at,
        })

    return DashboardResponse(
        total_claims_30d=total,
        stp_rate=round(stp_rate, 1),
        avg_processing_seconds=round(avg_secs, 1),
        fraud_high=fraud_high,
        fraud_medium=fraud_medium,
        fraud_low=fraud_low,
        avg_repair_cost=round(avg_repair, 0),
        claims_by_status=claims_by_status,
        claims_by_type=claims_by_type,
        claims_trend=claims_trend,
        fraud_distribution=fraud_distribution,
        processing_time_buckets=processing_time_buckets,
        recent_claims=recent_claims,
    )
