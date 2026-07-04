"""
SQLAlchemy ORM table definitions.

Mirrors the Pydantic models but lives in the persistence layer.
Vendors and routing logs are the two core tables.
"""

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class VendorRow(Base):
    """Persisted vendor registration."""

    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    capability: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_per_request: Mapped[float] = mapped_column(Float, nullable=False)
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    supported_features: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )  # JSON-encoded list
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RoutingLogRow(Base):
    """Persisted routing decision log — every /route call produces one row."""

    __tablename__ = "routing_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy_used: Mapped[str] = mapped_column(String(32), nullable=False)
    vendor_used: Mapped[str | None] = mapped_column(String(128), nullable=True)
    outcome: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # SUCCESS | FAILED
    routing_reason: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    attempts_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )  # JSON-encoded attempts array
    filter_reasons_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )  # JSON-encoded filter exclusions
    request_payload_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
