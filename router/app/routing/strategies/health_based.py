"""
Health-based routing — order by descending composite health score.

Composite score = f(successRate, errorRate, p95Latency, circuitState).
Vendors that are performing well get the highest score and are tried first.
"""

from app.models.vendor import VendorConfig
from app.reliability.circuit_breaker import CircuitBreakerRegistry, CircuitState
from app.reliability.metrics import MetricsCollector
from app.routing.strategies.base import RoutingStrategy


class HealthBasedStrategy(RoutingStrategy):
    @property
    def name(self) -> str:
        return "health_based"

    def rank(self, vendors: list[VendorConfig], capability: str, **context) -> list[VendorConfig]:
        metrics: MetricsCollector = context.get("metrics")
        breakers: CircuitBreakerRegistry = context.get("circuit_breakers")

        if metrics is None:
            return sorted(vendors, key=lambda v: v.priority)

        def health_score(v: VendorConfig) -> float:
            """
            Composite health score (0–100, higher = healthier).

            Components:
            - Success rate: 0–40 points (most important — are requests actually succeeding?)
            - Error rate penalty: 0–20 points deducted
            - Latency score: 0–25 points (lower p95 = better)
            - Circuit state: 0–15 points (CLOSED = full, HALF_OPEN = partial, OPEN = 0)
            """
            m = metrics.get_metrics(v.name, "short")
            score = 0.0

            # Success rate component (0–40)
            score += m.success_rate * 40

            # Error rate penalty (0–20 deducted)
            score -= m.error_rate * 20

            # Latency component (0–25): lower is better
            if m.latency_p95 is not None and m.latency_p95 > 0:
                # Normalize: 0ms = 25pts, 5000ms+ = 0pts
                latency_score = max(0, 25 * (1 - m.latency_p95 / 5000))
                score += latency_score
            else:
                score += 15  # No data yet — neutral score

            # Circuit state component (0–15)
            if breakers:
                cb = breakers.get(v.name)
                if cb.state == CircuitState.CLOSED:
                    score += 15
                elif cb.state == CircuitState.HALF_OPEN:
                    score += 7
                # OPEN = 0 (should have been filtered, but defensive)
            else:
                score += 15  # No circuit breaker data — assume healthy

            return score

        return sorted(vendors, key=health_score, reverse=True)
