"""
Application configuration and named constants.

Every threshold, window size, and default lives here — no magic numbers
in business logic. Each default has a rationale comment.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration loaded from environment variables with sensible defaults."""

    # --- Server ---
    APP_NAME: str = "Vendor Routing Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./vendor_routing.db"

    # --- Mock vendors base URL (overridden by docker-compose) ---
    MOCK_VENDOR_BASE_URL: str = "http://localhost:9000"

    # --- Circuit Breaker ---
    # Trip to OPEN after this many consecutive failures in the window.
    # 5 strikes balances sensitivity (catches real outages quickly)
    # against resilience to transient blips.
    CIRCUIT_FAIL_THRESHOLD: int = 5

    # Trip to OPEN if error rate in the window exceeds this fraction.
    # 50 % means the vendor is failing half its requests — clearly degraded.
    CIRCUIT_ERROR_RATE: float = 0.50

    # Seconds to wait in OPEN before allowing a single trial (HALF_OPEN).
    # 30 s is long enough for most transient issues to clear, short enough
    # to recover quickly.
    CIRCUIT_COOLDOWN_SECONDS: int = 30

    # --- Metrics sliding windows ---
    # Short window for real-time latency/error detection in the filter pipeline.
    METRICS_WINDOW_SHORT_SECONDS: int = 60

    # Longer window for trend analysis and the dashboard charts.
    METRICS_WINDOW_LONG_SECONDS: int = 300

    # --- Rate limiter ---
    # Token bucket refill uses vendor.rateLimitPerMinute / 60 tokens/second.
    # No extra config needed — the bucket capacity comes from the vendor config.

    # --- Routing defaults ---
    # Default strategy when none is specified in the routing config.
    DEFAULT_STRATEGY: str = "priority"

    # Whether to attempt the next candidate on failure by default.
    DEFAULT_FAILOVER: bool = True

    # --- Logging ---
    # Maximum routing logs returned per page.
    LOG_PAGE_SIZE: int = 50

    # --- Agentic AI ---
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = Settings()
