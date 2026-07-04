"""
Feature-based routing — vendors are pre-filtered by the pipeline,
then ordered by priority among those that support the required features.
"""

from app.models.vendor import VendorConfig
from app.routing.strategies.base import RoutingStrategy


class FeatureBasedStrategy(RoutingStrategy):
    @property
    def name(self) -> str:
        return "feature_based"

    def rank(self, vendors: list[VendorConfig], capability: str, **context) -> list[VendorConfig]:
        # By the time we get here, vendors have already been filtered
        # to only those supporting the required features.
        # Among the survivors, order by priority (lower = better).
        return sorted(vendors, key=lambda v: v.priority)
