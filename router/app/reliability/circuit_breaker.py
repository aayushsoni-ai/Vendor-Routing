"""
Circuit Breaker — per-vendor health state machine.

Three states:
- CLOSED (normal): Trip to OPEN when failures in the window ≥ threshold
  OR error rate ≥ error_rate_threshold.
- OPEN (skip vendor entirely in filter pipeline): After cooldown,
  move to HALF_OPEN.
- HALF_OPEN: Allow one trial request. Success → CLOSED; failure → OPEN again.

Pattern reference: Michael Nygard's "Release It!" circuit breaker pattern.
The thresholds live in config.py so there are no magic numbers here.
"""

import time
from enum import Enum

from app.config import settings


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Per-vendor circuit breaker."""

    def __init__(self, vendor_name: str):
        self.vendor_name = vendor_name
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._total_count = 0
        self._last_failure_time: float = 0
        self._opened_at: float = 0
        self._threshold = settings.CIRCUIT_FAIL_THRESHOLD
        self._error_rate_threshold = settings.CIRCUIT_ERROR_RATE
        self._cooldown = settings.CIRCUIT_COOLDOWN_SECONDS

    @property
    def is_open(self) -> bool:
        """Should this vendor be skipped?"""
        if self.state == CircuitState.OPEN:
            # Check if cooldown has passed → transition to HALF_OPEN
            if time.time() - self._opened_at >= self._cooldown:
                self.state = CircuitState.HALF_OPEN
                return False  # Allow one trial
            return True
        return False

    @property
    def is_half_open(self) -> bool:
        return self.state == CircuitState.HALF_OPEN

    def on_success(self) -> None:
        """Record a successful vendor call."""
        self._success_count += 1
        self._total_count += 1

        if self.state == CircuitState.HALF_OPEN:
            # Trial succeeded — close the circuit
            self.state = CircuitState.CLOSED
            self._failure_count = 0

    def on_failure(self) -> None:
        """Record a failed vendor call. May trip the circuit."""
        self._failure_count += 1
        self._total_count += 1
        self._last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Trial failed — reopen
            self._trip()
            return

        # Check consecutive failure threshold
        if self._failure_count >= self._threshold:
            self._trip()
            return

        # Check error rate threshold (only if we have enough data)
        if self._total_count >= 5:  # Need a minimum sample size
            error_rate = self._failure_count / self._total_count
            if error_rate >= self._error_rate_threshold:
                self._trip()

    def _trip(self) -> None:
        """Open the circuit."""
        self.state = CircuitState.OPEN
        self._opened_at = time.time()

    def reset(self) -> None:
        """Manually reset the circuit (e.g. when vendor config changes)."""
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._total_count = 0

    def to_dict(self) -> dict:
        """Serialize for the /vendor-metrics API."""
        return {
            "state": self.state.value,
            "failureCount": self._failure_count,
            "lastFailureTime": self._last_failure_time or None,
            "openedAt": self._opened_at or None,
        }


class CircuitBreakerRegistry:
    """Manages per-vendor circuit breakers."""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, vendor_name: str) -> CircuitBreaker:
        if vendor_name not in self._breakers:
            self._breakers[vendor_name] = CircuitBreaker(vendor_name)
        return self._breakers[vendor_name]

    def get_all(self) -> dict[str, CircuitBreaker]:
        return dict(self._breakers)


# Singleton
circuit_breakers = CircuitBreakerRegistry()
