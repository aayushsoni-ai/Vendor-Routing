"""Priority-based routing — order by ascending priority (lower = first)."""

from app.models.vendor import VendorConfig
from app.routing.strategies.base import RoutingStrategy


class PriorityStrategy(RoutingStrategy):
    @property
    def name(self) -> str:
        return "priority"

    def rank(self, vendors: list[VendorConfig], capability: str, **context) -> list[VendorConfig]:
        return sorted(vendors, key=lambda v: v.priority)
