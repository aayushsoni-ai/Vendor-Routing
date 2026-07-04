"""
Canonical response schemas.

Every /route call returns one of these shapes regardless of which
vendor actually served the request. The normalizer (vendors/normalizer.py)
maps vendor-specific responses into these canonical forms.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class AttemptRecord(BaseModel):
    """One vendor attempt in the failover chain."""

    vendor: str
    outcome: str  # SUCCESS | TIMEOUT | ERROR_5XX | RATE_LIMITED | UNSUPPORTED_FEATURE
    latency_ms: Optional[int] = Field(default=None, alias="latencyMs")
    error: Optional[str] = None

    model_config = {"populate_by_name": True}


class RouteSuccessResponse(BaseModel):
    """Standardized success response from POST /route."""

    status: str = "SUCCESS"
    request_id: str = Field(alias="requestId")
    capability: str
    vendor_used: str = Field(alias="vendorUsed")
    routing_reason: str = Field(alias="routingReason")
    strategy_used: str = Field(alias="strategyUsed")
    latency_ms: int = Field(alias="latencyMs")
    cost: float
    attempts: list[AttemptRecord]
    response: dict  # canonical per-capability response (e.g. panStatus, nameMatch)

    model_config = {"populate_by_name": True}


class ErrorDetail(BaseModel):
    code: str
    message: str


class RouteFailureResponse(BaseModel):
    """Standardized failure response from POST /route."""

    status: str = "FAILED"
    request_id: str = Field(alias="requestId")
    capability: str
    routing_reason: str = Field(alias="routingReason")
    attempts: list[AttemptRecord]
    error: ErrorDetail

    model_config = {"populate_by_name": True}


# --- Canonical per-capability response shapes ---


class PanVerificationResult(BaseModel):
    """Canonical PAN verification response."""

    pan_status: str = Field(alias="panStatus")  # VALID | INVALID | NOT_FOUND
    name_match: Optional[bool] = Field(default=None, alias="nameMatch")
    dob_match: Optional[bool] = Field(default=None, alias="dobMatch")

    model_config = {"populate_by_name": True}
