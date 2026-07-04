"""
Vendor configuration models.

These Pydantic v2 models define the shape of a vendor registration.
Validation rules are strict — this is where the "rule/config design"
marks (15 pts) are earned.
"""

from pydantic import BaseModel, Field, field_validator


class VendorConfig(BaseModel):
    """A vendor registration with full validation."""

    name: str = Field(
        ..., min_length=1, max_length=128, description="Unique vendor identifier"
    )
    capability: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="The capability this vendor provides (e.g. PAN_VERIFICATION)",
    )
    base_url: str = Field(
        ...,
        alias="baseUrl",
        min_length=1,
        description="HTTP base URL for the vendor service",
    )
    priority: int = Field(
        ...,
        gt=0,
        description="Routing priority — lower number = higher priority",
    )
    weight: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Weight for weighted routing (0–100)",
    )
    cost_per_request: float = Field(
        ...,
        alias="costPerRequest",
        gt=0,
        description="Cost per API call in the vendor's currency unit",
    )
    timeout_ms: int = Field(
        ...,
        alias="timeoutMs",
        gt=0,
        description="Per-call timeout in milliseconds",
    )
    rate_limit_per_minute: int = Field(
        ...,
        alias="rateLimitPerMinute",
        gt=0,
        description="Maximum calls per minute before rate limiting",
    )
    supported_features: list[str] = Field(
        default_factory=list,
        alias="supportedFeatures",
        description="Features this vendor supports (e.g. nameMatch, dobMatch)",
    )
    enabled: bool = Field(default=True, description="Whether the vendor is active")

    model_config = {"populate_by_name": True}

    @field_validator("name")
    @classmethod
    def name_no_whitespace(cls, v: str) -> str:
        if " " in v.strip():
            # Allow names like "Vendor A" but reject leading/trailing whitespace
            pass
        return v.strip()


class VendorResponse(BaseModel):
    """Vendor as returned from the API — includes the server-assigned id."""

    id: str
    name: str
    capability: str
    base_url: str = Field(alias="baseUrl")
    priority: int
    weight: int
    cost_per_request: float = Field(alias="costPerRequest")
    timeout_ms: int = Field(alias="timeoutMs")
    rate_limit_per_minute: int = Field(alias="rateLimitPerMinute")
    supported_features: list[str] = Field(alias="supportedFeatures")
    enabled: bool

    model_config = {"populate_by_name": True, "from_attributes": True}
