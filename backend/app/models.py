import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, Text, text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID

TSTZ = DateTime(timezone=True)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional link to the customer's primary city (for shop recommendations)
    city_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cities.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TSTZ, default=lambda: datetime.now(timezone.utc))

    policies: Mapped[list["Policy"]] = relationship(back_populates="customer", lazy="selectin")
    city: Mapped[Optional["City"]] = relationship(back_populates="customers", lazy="selectin")


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"), nullable=False)
    policy_number: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)  # active|lapsed|cancelled
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TSTZ, default=lambda: datetime.now(timezone.utc))

    customer: Mapped["Customer"] = relationship(back_populates="policies", lazy="selectin")
    coverages: Mapped[list["Coverage"]] = relationship(back_populates="policy", lazy="selectin")
    claims: Mapped[list["Claim"]] = relationship(back_populates="policy", lazy="selectin")


class Coverage(Base):
    __tablename__ = "coverages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policies.id"), nullable=False)
    coverage_type: Mapped[str] = mapped_column(Text, nullable=False)  # collision|comprehensive|liability|roadside
    deductible_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    limit_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_severity: Mapped[str | None] = mapped_column(Text, nullable=True)  # minor|moderate|severe
    created_at: Mapped[datetime] = mapped_column(TSTZ, default=lambda: datetime.now(timezone.utc))

    policy: Mapped["Policy"] = relationship(back_populates="coverages", lazy="selectin")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_number: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    policy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policies.id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="intake")  # intake|needs_info|accepted|denied|escalated
    incident_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    incident_type: Mapped[str | None] = mapped_column(Text, nullable=True)  # collision|theft|weather|glass|unknown
    description: Mapped[str] = mapped_column(Text, nullable=False)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    fraud_risk_level: Mapped[str | None] = mapped_column(Text, nullable=True)  # high|medium|low
    fraud_risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    estimated_cost_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_cost_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TSTZ, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        TSTZ,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    policy: Mapped["Policy"] = relationship(back_populates="claims", lazy="selectin")
    events: Mapped[list["ClaimEvent"]] = relationship(back_populates="claim", lazy="selectin", order_by="ClaimEvent.created_at.desc()")


class ClaimEvent(Base):
    __tablename__ = "claim_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("claims.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)  # note|question|answer|tool_result|decision|error|status_change
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(TSTZ, default=lambda: datetime.now(timezone.utc))

    claim: Mapped["Claim"] = relationship(back_populates="events", lazy="selectin")


# ---------------------------------------------
# New entities for city & approved repair shops
# ---------------------------------------------


class City(Base):
    __tablename__ = "cities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    province: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TSTZ, default=lambda: datetime.now(timezone.utc))

    customers: Mapped[list["Customer"]] = relationship(back_populates="city", lazy="selectin")
    repair_shops: Mapped[list["RepairShop"]] = relationship(back_populates="city", lazy="selectin")


class RepairShop(Base):
    __tablename__ = "repair_shops"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=4)  # 1-5
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(TSTZ, default=lambda: datetime.now(timezone.utc))

    city: Mapped["City"] = relationship(back_populates="repair_shops", lazy="selectin")
