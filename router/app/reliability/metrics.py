"""
Reliability — Sliding-window metrics collector.

Keeps a time-based deque of (timestamp, outcome, latencyMs) records per vendor,
pruned to a configurable window. Computes on read:
- requestCount, successRate, errorRate
- latencyP50, latencyP95, latencyP99 (sort the window)
- availability (derived from circuit state + success ratio)

These metrics feed: lowest_latency strategy, health_based strategy,
the maxLatencyMs filter, /vendor-metrics API, and the agent's "detect unhealthy."
"""

import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

from app.config import settings


@dataclass
class MetricRecord:
    """One datapoint in the sliding window."""
    timestamp: float
    outcome: str  # SUCCESS | TIMEOUT | ERROR_5XX | RATE_LIMITED | etc.
    latency_ms: int


@dataclass
class VendorMetrics:
    """Computed metrics for a single vendor at read time."""
    vendor_name: str
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    error_rate: float = 0.0
    latency_p50: Optional[int] = None
    latency_p95: Optional[int] = None
    latency_p99: Optional[int] = None
    avg_latency_ms: Optional[float] = None
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None


class MetricsCollector:
    """
    Sliding-window metrics collector.

    Two windows are maintained per vendor:
    - Short (60s) for real-time filter decisions
    - Long (5min) for dashboard charts and trend analysis

    Thread-safety note: in an async single-thread model (uvicorn default),
    this is safe without locks. For multi-worker, use shared state or Redis.
    """

    def __init__(self):
        self._short_window: dict[str, deque[MetricRecord]] = defaultdict(deque)
        self._long_window: dict[str, deque[MetricRecord]] = defaultdict(deque)
        self._short_seconds = settings.METRICS_WINDOW_SHORT_SECONDS
        self._long_seconds = settings.METRICS_WINDOW_LONG_SECONDS

    def record_success(self, vendor_name: str, latency_ms: int) -> None:
        """Record a successful vendor call."""
        record = MetricRecord(
            timestamp=time.time(),
            outcome="SUCCESS",
            latency_ms=latency_ms,
        )
        self._short_window[vendor_name].append(record)
        self._long_window[vendor_name].append(record)

    def record_failure(self, vendor_name: str, outcome: str, latency_ms: int = 0) -> None:
        """Record a failed vendor call (timeout, 5xx, rate-limited, etc.)."""
        record = MetricRecord(
            timestamp=time.time(),
            outcome=outcome,
            latency_ms=latency_ms,
        )
        self._short_window[vendor_name].append(record)
        self._long_window[vendor_name].append(record)

    def get_metrics(self, vendor_name: str, window: str = "short") -> VendorMetrics:
        """
        Compute metrics for a vendor from the given window.

        Args:
            vendor_name: Which vendor
            window: "short" (60s) or "long" (5min)
        """
        self._prune(vendor_name)

        records = list(
            self._short_window[vendor_name]
            if window == "short"
            else self._long_window[vendor_name]
        )

        metrics = VendorMetrics(vendor_name=vendor_name)
        if not records:
            return metrics

        metrics.request_count = len(records)
        metrics.success_count = sum(1 for r in records if r.outcome == "SUCCESS")
        metrics.failure_count = metrics.request_count - metrics.success_count
        metrics.success_rate = (
            metrics.success_count / metrics.request_count if metrics.request_count > 0 else 0.0
        )
        metrics.error_rate = 1.0 - metrics.success_rate

        # Latency percentiles (from successful calls only — failed calls may have 0 latency)
        latencies = sorted(r.latency_ms for r in records if r.outcome == "SUCCESS" and r.latency_ms > 0)
        if latencies:
            metrics.latency_p50 = self._percentile(latencies, 50)
            metrics.latency_p95 = self._percentile(latencies, 95)
            metrics.latency_p99 = self._percentile(latencies, 99)
            metrics.avg_latency_ms = round(statistics.mean(latencies), 1)

        # Last error
        errors = [r for r in records if r.outcome != "SUCCESS"]
        if errors:
            last = errors[-1]
            metrics.last_error = last.outcome
            metrics.last_error_time = last.timestamp

        return metrics

    def get_p95_latency(self, vendor_name: str) -> Optional[int]:
        """Quick accessor used by the maxLatencyMs filter."""
        m = self.get_metrics(vendor_name, "short")
        return m.latency_p95

    def get_error_rate(self, vendor_name: str) -> float:
        """Quick accessor used by the circuit breaker."""
        m = self.get_metrics(vendor_name, "short")
        return m.error_rate

    def get_all_vendor_names(self) -> list[str]:
        """Return all vendors that have any recorded metrics."""
        return list(set(list(self._short_window.keys()) + list(self._long_window.keys())))

    def _prune(self, vendor_name: str) -> None:
        """Remove expired records from both windows."""
        now = time.time()
        short_cutoff = now - self._short_seconds
        long_cutoff = now - self._long_seconds

        sw = self._short_window[vendor_name]
        while sw and sw[0].timestamp < short_cutoff:
            sw.popleft()

        lw = self._long_window[vendor_name]
        while lw and lw[0].timestamp < long_cutoff:
            lw.popleft()

    @staticmethod
    def _percentile(sorted_values: list[int], p: int) -> int:
        """Compute the p-th percentile from a sorted list."""
        if not sorted_values:
            return 0
        k = (len(sorted_values) - 1) * (p / 100.0)
        f = int(k)
        c = f + 1
        if c >= len(sorted_values):
            return sorted_values[-1]
        d = k - f
        return int(sorted_values[f] + d * (sorted_values[c] - sorted_values[f]))


# Singleton — shared across the app
metrics_collector = MetricsCollector()
