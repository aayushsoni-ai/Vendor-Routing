"""
Log models for routing decisions.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.responses import AttemptRecord


class RoutingDecisionLog(BaseModel):
    """A complete routing decision record — persisted after every /route call."""

    id: str
    request_id: str = Field(alias="requestId")
    capability: str
    strategy_used: str = Field(alias="strategyUsed")
    vendor_used: Optional[str] = Field(default=None, alias="vendorUsed")
    outcome: str  # SUCCESS | FAILED
    routing_reason: str = Field(alias="routingReason")
    latency_ms: Optional[int] = Field(default=None, alias="latencyMs")
    cost: Optional[float] = None
    attempts: list[AttemptRecord]
    filter_reasons: dict[str, str] = Field(
        default_factory=dict, alias="filterReasons"
    )  # vendor → reason excluded
    created_at: datetime = Field(alias="createdAt")

    model_config = {"populate_by_name": True, "from_attributes": True}
