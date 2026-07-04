"""
Token Bucket Rate Limiter — per-vendor rate limiting.

Bucket capacity = vendor.rateLimitPerMinute.
Refill rate = capacity / 60 tokens per second.
try_acquire() consumes one token; empty bucket → vendor is rate-limited.

The Token Bucket algorithm is chosen over fixed-window because it handles
burst traffic more gracefully — a vendor that's been idle accumulates
tokens and can absorb a short burst without tripping the limit.
"""

import time
from dataclasses import dataclass


@dataclass
class TokenBucket:
    """A single vendor's rate limiter."""

    vendor_name: str
    capacity: int  # max tokens (= rateLimitPerMinute)
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float

    def try_acquire(self) -> bool:
        """
        Try to consume one token. Returns True if allowed, False if rate-limited.
        Refills tokens based on elapsed time before checking.
        """
        self._refill()
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

    def _refill(self) -> None:
        """Add tokens based on time elapsed since last refill."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

    @property
    def available_tokens(self) -> int:
        """Current token count (after refill)."""
        self._refill()
        return int(self.tokens)

    def to_dict(self) -> dict:
        return {
            "capacity": self.capacity,
            "availableTokens": self.available_tokens,
            "refillRate": round(self.refill_rate, 2),
        }


class RateLimiterRegistry:
    """Manages per-vendor token buckets."""

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}

    def get_or_create(self, vendor_name: str, rate_limit_per_minute: int) -> TokenBucket:
        """Get or create a token bucket for a vendor."""
        if vendor_name not in self._buckets:
            self._buckets[vendor_name] = TokenBucket(
                vendor_name=vendor_name,
                capacity=rate_limit_per_minute,
                tokens=float(rate_limit_per_minute),  # Start full
                refill_rate=rate_limit_per_minute / 60.0,
                last_refill=time.time(),
            )
        return self._buckets[vendor_name]

    def try_acquire(self, vendor_name: str, rate_limit_per_minute: int) -> bool:
        """Convenience: get-or-create and try to acquire in one call."""
        bucket = self.get_or_create(vendor_name, rate_limit_per_minute)
        return bucket.try_acquire()

    def get_all(self) -> dict[str, TokenBucket]:
        return dict(self._buckets)


# Singleton
rate_limiters = RateLimiterRegistry()
