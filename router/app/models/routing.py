"""
Routing configuration and request models.

Defines the Strategy enum, routing config per capability,
route request shape, and per-request requirement overrides.
"""

from enum import Enum
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, field_validator, model_validator


class Strategy(str, Enum):
    """All supported routing strategies."""

    PRIORITY = "priority"
    WEIGHTED = "weighted"
    LOWEST_LATENCY = "lowest_latency"
    LOWEST_COST = "lowest_cost"
    FAILOVER = "failover"
    ROUND_ROBIN = "round_robin"
    FEATURE_BASED = "feature_based"
    HEALTH_BASED = "health_based"


class RoutingRequirements(BaseModel):
    """
    Per-request requirement overrides.
    All fields are optional — the caller only sends what they care about.
    """

    max_latency_ms: Optional[int] = Field(
        default=None,
        alias="maxLatencyMs",
        gt=0,
        description="Hard filter: drop vendors whose recent p95 exceeds this",
    )
    prefer_low_cost: Optional[bool] = Field(
        default=None,
        alias="preferLowCost",
        description="Soft override: order by lowest cost",
    )
    required_features: Optional[list[str]] = Field(
        default=None,
        alias="requiredFeatures",
        description="Hard filter: vendor must support all listed features",
    )
    strategy: Optional[Strategy] = Field(
        default=None,
        description="Per-request strategy override",
    )

    model_config = {"populate_by_name": True}


class RouteRequest(BaseModel):
    """
    The unified routing request — body of POST /route.
    """

    capability: str = Field(
        ...,
        min_length=1,
        description="Which capability to route (e.g. PAN_VERIFICATION)",
    )
    payload: dict = Field(
        ...,
        description="Vendor-specific payload to forward",
    )
    requirements: Optional[RoutingRequirements] = Field(
        default=None,
        description="Optional per-request routing requirements",
    )


class RoutingConfig(BaseModel):
    """
    Per-capability routing configuration.
    Used in JSON config files and as the shape for agent-generated configs.
    """

    capability: str = Field(..., min_length=1)
    strategy: Strategy = Field(default=Strategy.PRIORITY)
    failover: bool = Field(default=True)

    @model_validator(mode="after")
    def validate_config(self):
        return self
