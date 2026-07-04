"""Lowest cost routing — order by ascending costPerRequest."""

from app.models.vendor import VendorConfig
from app.routing.strategies.base import RoutingStrategy


class LowestCostStrategy(RoutingStrategy):
    @property
    def name(self) -> str:
        return "lowest_cost"

    def rank(self, vendors: list[VendorConfig], capability: str, **context) -> list[VendorConfig]:
        return sorted(vendors, key=lambda v: v.cost_per_request)
