import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


# --- City ---
class CityOut(BaseModel):
    id: uuid.UUID
    name: str
    province: str

    model_config = {"from_attributes": True}


# --- Customer ---
class CustomerOut(BaseModel):
    id: uuid.UUID
    full_name: str
    created_at: datetime
    city: CityOut | None = None

    model_config = {"from_attributes": True}


# --- Coverage ---
class CoverageOut(BaseModel):
    id: uuid.UUID
    coverage_type: str
    deductible_amount: Optional[int] = None
    limit_amount: Optional[int] = None
    max_severity: Optional[str] = None

    model_config = {"from_attributes": True}


# --- Policy ---
class PolicyOut(BaseModel):
    id: uuid.UUID
    policy_number: str
    status: str
    start_date: date
    end_date: date
    customer: CustomerOut
    coverages: list[CoverageOut]

    model_config = {"from_attributes": True}


# --- Claim Event ---
class ClaimEventOut(BaseModel):
    id: uuid.UUID
    event_type: str
    message: str
    payload: dict[str, Any] = {}
    created_at: datetime

    model_config = {"from_attributes": True}


class ClaimEventCreate(BaseModel):
    event_type: str
    message: str
    payload: Optional[dict[str, Any]] = None


# --- Claim ---
class ClaimCreate(BaseModel):
    policy_number: str
    description: str
    incident_date: Optional[date] = None
    incident_type: Optional[str] = None


class ClaimOut(BaseModel):
    id: uuid.UUID
    claim_number: str
    policy_id: uuid.UUID
    status: str
    incident_date: Optional[date] = None
    incident_type: Optional[str] = None
    description: str
    decision_reason: Optional[str] = None
    fraud_risk_level: Optional[str] = None
    fraud_risk_score: Optional[int] = None
    estimated_cost_min: Optional[float] = None
    estimated_cost_max: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    events: list[ClaimEventOut] = []

    model_config = {"from_attributes": True}


class ClaimCreateResponse(BaseModel):
    id: uuid.UUID
    claim_number: str
    status: str

    model_config = {"from_attributes": True}


class ClaimPatch(BaseModel):
    status: Optional[str] = None
    incident_date: Optional[date] = None
    incident_type: Optional[str] = None
    decision_reason: Optional[str] = None
    description: Optional[str] = None
    fraud_risk_level: Optional[str] = None
    fraud_risk_score: Optional[int] = None
    estimated_cost_min: Optional[float] = None
    estimated_cost_max: Optional[float] = None


# --- Claim Summary (lightweight, for list endpoints) ---
class ClaimSummaryOut(BaseModel):
    id: uuid.UUID
    claim_number: str
    status: str
    incident_date: Optional[date] = None
    incident_type: Optional[str] = None
    description: str
    fraud_risk_level: Optional[str] = None
    fraud_risk_score: Optional[int] = None
    estimated_cost_min: Optional[float] = None
    estimated_cost_max: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Repair Shop ---
class RepairShopOut(BaseModel):
    id: uuid.UUID
    name: str
    address: str
    phone: str
    email: Optional[str] = None
    rating: int

    model_config = {"from_attributes": True}


# --- Dashboard ---
class ClaimsByStatus(BaseModel):
    status: str
    count: int


class ClaimsByType(BaseModel):
    incident_type: str
    count: int


class ClaimsTrendDay(BaseModel):
    date: str
    accepted: int = 0
    denied: int = 0
    escalated: int = 0
    needs_info: int = 0
    intake: int = 0


class FraudBucket(BaseModel):
    level: str
    count: int


class ProcessingTimeBucket(BaseModel):
    bucket: str
    count: int


class RecentClaim(BaseModel):
    id: uuid.UUID
    claim_number: str
    status: str
    incident_type: Optional[str] = None
    customer_name: str
    fraud_risk_level: Optional[str] = None
    estimated_cost_mid: Optional[float] = None
    created_at: datetime


class DashboardResponse(BaseModel):
    total_claims_30d: int
    stp_rate: float
    avg_processing_seconds: float
    fraud_high: int
    fraud_medium: int
    fraud_low: int
    avg_repair_cost: float
    claims_by_status: list[ClaimsByStatus]
    claims_by_type: list[ClaimsByType]
    claims_trend: list[ClaimsTrendDay]
    fraud_distribution: list[FraudBucket]
    processing_time_buckets: list[ProcessingTimeBucket]
    recent_claims: list[RecentClaim]
