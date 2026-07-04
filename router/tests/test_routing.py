# pyrefly: ignore [missing-import]
import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from app.models.vendor import VendorConfig
from app.models.routing import RouteRequest, RoutingRequirements, Strategy
from app.reliability.circuit_breaker import CircuitBreaker, CircuitState
from app.reliability.rate_limiter import TokenBucket, RateLimiterRegistry
from app.reliability.metrics import MetricsCollector
from app.routing.pipeline import filter_vendors
from app.routing.strategies.priority import PriorityStrategy
from app.routing.strategies.lowest_cost import LowestCostStrategy
from app.routing.strategies.weighted import WeightedStrategy

# --- 1. Test Pydantic validation ---
def test_vendor_config_validation():
    # Valid config
    config = VendorConfig(
        name="VendorA",
        capability="PAN_VERIFICATION",
        baseUrl="http://localhost:9000",
        priority=1,
        weight=70,
        costPerRequest=1.5,
        timeoutMs=2000,
        rateLimitPerMinute=100,
        supportedFeatures=["nameMatch", "dobMatch"]
    )
    assert config.name == "VendorA"
    assert config.weight == 70

    # Invalid weights
    with pytest.raises(ValueError):
        VendorConfig(
            name="VendorA",
            capability="PAN_VERIFICATION",
            baseUrl="http://localhost:9000",
            priority=1,
            weight=150,  # weight > 100
            costPerRequest=1.5,
            timeoutMs=2000,
            rateLimitPerMinute=100
        )

# --- 2. Test strategies ---
def test_priority_strategy():
    v1 = VendorConfig(name="V1", capability="PAN", baseUrl="http://h", priority=2, costPerRequest=1, timeoutMs=1000, rateLimitPerMinute=10)
    v2 = VendorConfig(name="V2", capability="PAN", baseUrl="http://h", priority=1, costPerRequest=2, timeoutMs=1000, rateLimitPerMinute=10)
    
    strategy = PriorityStrategy()
    ranked = strategy.rank([v1, v2], "PAN")
    assert ranked[0].name == "V2"
    assert ranked[1].name == "V1"

def test_lowest_cost_strategy():
    v1 = VendorConfig(name="V1", capability="PAN", baseUrl="http://h", priority=2, costPerRequest=2.5, timeoutMs=1000, rateLimitPerMinute=10)
    v2 = VendorConfig(name="V2", capability="PAN", baseUrl="http://h", priority=1, costPerRequest=1.2, timeoutMs=1000, rateLimitPerMinute=10)
    
    strategy = LowestCostStrategy()
    ranked = strategy.rank([v1, v2], "PAN")
    assert ranked[0].name == "V2"
    assert ranked[1].name == "V1"

# --- 3. Test reliability components ---
def test_circuit_breaker():
    cb = CircuitBreaker("TestVendor")
    assert cb.state == CircuitState.CLOSED
    assert not cb.is_open

    # Simulate 5 failures
    for _ in range(5):
        cb.on_failure()
    
    assert cb.state == CircuitState.OPEN
    assert cb.is_open

    # Simulate cooldown bypass / check is_open
    cb._opened_at = time.time() - 40  # 40 seconds ago (cooldown is 30)
    assert not cb.is_open  # transitions to HALF_OPEN when checked
    assert cb.state == CircuitState.HALF_OPEN

    # Success should close it
    cb.on_success()
    assert cb.state == CircuitState.CLOSED

def test_rate_limiter():
    limiter = RateLimiterRegistry()
    
    # Bucket capacity 2, refilling 2/minute
    bucket = limiter.get_or_create("VendorA", 2)
    bucket.tokens = 2.0  # initialize to capacity
    
    assert limiter.try_acquire("VendorA", 2)
    assert limiter.try_acquire("VendorA", 2)
    assert not limiter.try_acquire("VendorA", 2)  # exhausted

# --- 4. Test Filter pipeline ---
def test_filter_pipeline():
    v1 = VendorConfig(name="V1", capability="PAN", baseUrl="http://h", priority=1, costPerRequest=1, timeoutMs=1000, rateLimitPerMinute=10, supportedFeatures=["featA"])
    v2 = VendorConfig(name="V2", capability="PAN", baseUrl="http://h", priority=2, costPerRequest=1, timeoutMs=1000, rateLimitPerMinute=10, enabled=False)
    
    from app.reliability.circuit_breaker import CircuitBreakerRegistry
    breakers = CircuitBreakerRegistry()
    limiters = RateLimiterRegistry()
    metrics = MetricsCollector()
    
    req = RoutingRequirements(requiredFeatures=["featA"])
    
    survivors, reasons = filter_vendors([v1, v2], req, breakers, limiters, metrics)
    assert len(survivors) == 1
    assert survivors[0].name == "V1"
    assert reasons["V2"] == "disabled"
