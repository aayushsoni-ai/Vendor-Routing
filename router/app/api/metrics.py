"""
GET /vendor-metrics — live per-vendor metrics + circuit state.
"""

from typing import Optional

from fastapi import APIRouter, Query

from app.reliability.circuit_breaker import circuit_breakers
from app.reliability.metrics import metrics_collector
from app.reliability.rate_limiter import rate_limiters

router = APIRouter(tags=["Metrics"])


@router.get("/vendor-metrics")
async def get_vendor_metrics(
    vendor: Optional[str] = Query(default=None, description="Filter by vendor name"),
    capability: Optional[str] = Query(default=None, description="Filter by capability"),
) -> dict:
    """
    Live per-vendor metrics: p50/p95/p99 latency, success/error rate,
    request count, circuit breaker state, and rate limiter status.
    """
    vendor_names = metrics_collector.get_all_vendor_names()

    if vendor:
        vendor_names = [v for v in vendor_names if v == vendor]

    result = {}
    for name in vendor_names:
        short_metrics = metrics_collector.get_metrics(name, "short")
        long_metrics = metrics_collector.get_metrics(name, "long")
        cb = circuit_breakers.get(name)
        rl_buckets = rate_limiters.get_all()
        rl = rl_buckets.get(name)

        result[name] = {
            "shortWindow": {
                "requestCount": short_metrics.request_count,
                "successRate": round(short_metrics.success_rate, 4),
                "errorRate": round(short_metrics.error_rate, 4),
                "latencyP50": short_metrics.latency_p50,
                "latencyP95": short_metrics.latency_p95,
                "latencyP99": short_metrics.latency_p99,
                "avgLatencyMs": short_metrics.avg_latency_ms,
                "lastError": short_metrics.last_error,
            },
            "longWindow": {
                "requestCount": long_metrics.request_count,
                "successRate": round(long_metrics.success_rate, 4),
                "errorRate": round(long_metrics.error_rate, 4),
                "latencyP50": long_metrics.latency_p50,
                "latencyP95": long_metrics.latency_p95,
                "latencyP99": long_metrics.latency_p99,
                "avgLatencyMs": long_metrics.avg_latency_ms,
            },
            "circuitBreaker": cb.to_dict(),
            "rateLimiter": rl.to_dict() if rl else None,
        }

    return {"metrics": result, "vendorCount": len(result)}
