"""
Failover routing — strict priority order.

Identical ranking to PriorityStrategy, but the *semantic intent* is
different: this strategy is chosen when the user's primary goal is
reliable delivery through the failover chain. The routing engine's
attempt loop does the actual failover; this strategy just ensures
vendors are tried in strict priority order.
"""

from app.models.vendor import VendorConfig
from app.routing.strategies.base import RoutingStrategy


class FailoverStrategy(RoutingStrategy):
    @property
    def name(self) -> str:
        return "failover"

    def rank(self, vendors: list[VendorConfig], capability: str, **context) -> list[VendorConfig]:
        return sorted(vendors, key=lambda v: v.priority)
