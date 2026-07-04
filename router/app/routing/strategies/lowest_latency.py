"""Lowest latency routing — order by ascending recent p95 latency."""

from app.models.vendor import VendorConfig
from app.reliability.metrics import MetricsCollector
from app.routing.strategies.base import RoutingStrategy


class LowestLatencyStrategy(RoutingStrategy):
    @property
    def name(self) -> str:
        return "lowest_latency"

    def rank(self, vendors: list[VendorConfig], capability: str, **context) -> list[VendorConfig]:
        metrics: MetricsCollector = context.get("metrics")
        if metrics is None:
            # No metrics available yet — fall back to priority
            return sorted(vendors, key=lambda v: v.priority)

        def latency_key(v: VendorConfig) -> int:
            p95 = metrics.get_p95_latency(v.name)
            # Vendors with no data yet get a neutral score (their configured timeout)
            return p95 if p95 is not None else v.timeout_ms

        return sorted(vendors, key=latency_key)
