"""
Filter Pipeline — removes ineligible vendors before ranking.

Applied in order, recording the reason each dropped vendor was excluded.
These reasons feed routingReason and the agent's explanations.

Filter order:
1. enabled == false → drop
2. Does not support all requiredFeatures → drop
3. Circuit breaker OPEN → drop
4. Over rate limit (token bucket empty) → drop
5. Recent p95 latency > maxLatencyMs → drop
"""

from typing import Optional

from app.models.vendor import VendorConfig
from app.models.routing import RoutingRequirements
from app.reliability.circuit_breaker import CircuitBreakerRegistry
from app.reliability.metrics import MetricsCollector
from app.reliability.rate_limiter import RateLimiterRegistry


def filter_vendors(
    vendors: list[VendorConfig],
    requirements: Optional[RoutingRequirements],
    circuit_breakers: CircuitBreakerRegistry,
    rate_limiters: RateLimiterRegistry,
    metrics: MetricsCollector,
) -> tuple[list[VendorConfig], dict[str, str]]:
    """
    Run the full filter pipeline.

    Returns:
        (survivors, filter_reasons) where filter_reasons maps
        excluded vendor names to the reason they were dropped.
    """
    survivors = []
    reasons: dict[str, str] = {}

    required_features = (
        requirements.required_features if requirements and requirements.required_features else []
    )
    max_latency_ms = (
        requirements.max_latency_ms if requirements else None
    )

    for vendor in vendors:
        # 1. Enabled check
        if not vendor.enabled:
            reasons[vendor.name] = "disabled"
            continue

        # 2. Feature support check
        if required_features:
            missing = [f for f in required_features if f not in vendor.supported_features]
            if missing:
                reasons[vendor.name] = f"missing features: {', '.join(missing)}"
                continue

        # 3. Circuit breaker check
        cb = circuit_breakers.get(vendor.name)
        if cb.is_open:
            reasons[vendor.name] = f"circuit breaker OPEN (tripped after failures)"
            continue

        # 4. Rate limit check (don't consume a token here — just check availability)
        bucket = rate_limiters.get_or_create(vendor.name, vendor.rate_limit_per_minute)
        if bucket.available_tokens < 1:
            reasons[vendor.name] = "rate limit exhausted"
            continue

        # 5. Latency threshold check
        if max_latency_ms is not None:
            p95 = metrics.get_p95_latency(vendor.name)
            if p95 is not None and p95 > max_latency_ms:
                reasons[vendor.name] = (
                    f"p95 latency {p95}ms exceeds threshold {max_latency_ms}ms"
                )
                continue

        survivors.append(vendor)

    return survivors, reasons
