"""
Round-robin routing — rotate through vendors evenly.

Keeps a per-capability cursor that advances on each call.
Provides fair distribution when all vendors are equally capable.
"""

from collections import defaultdict

from app.models.vendor import VendorConfig
from app.routing.strategies.base import RoutingStrategy


class RoundRobinStrategy(RoutingStrategy):
    def __init__(self):
        self._cursors: dict[str, int] = defaultdict(int)

    @property
    def name(self) -> str:
        return "round_robin"

    def rank(self, vendors: list[VendorConfig], capability: str, **context) -> list[VendorConfig]:
        if not vendors:
            return []

        # Sort by name for consistent ordering before rotation
        sorted_vendors = sorted(vendors, key=lambda v: v.name)
        n = len(sorted_vendors)
        cursor = self._cursors[capability] % n
        self._cursors[capability] = (cursor + 1) % n

        # Rotate: start from cursor position
        return sorted_vendors[cursor:] + sorted_vendors[:cursor]
