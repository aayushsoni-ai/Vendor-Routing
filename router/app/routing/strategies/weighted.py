"""
Weighted routing — smooth weighted round-robin to avoid clumping.

Uses the smooth weighted round-robin algorithm (Nginx-style): each vendor
has a current_weight that increases by its effective_weight each round.
The vendor with the highest current_weight wins and its current_weight
is reduced by the total weight. This produces an even distribution
over time without the clumping that naive weighted-random causes.

Seedable via context["seed"] for deterministic tests.
"""

import random
from collections import defaultdict

from app.models.vendor import VendorConfig
from app.routing.strategies.base import RoutingStrategy


class WeightedStrategy(RoutingStrategy):
    """Smooth weighted round-robin — distributes traffic proportionally without clumping."""

    def __init__(self):
        # Per-capability current weights for smooth round-robin
        self._current_weights: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    @property
    def name(self) -> str:
        return "weighted"

    def rank(self, vendors: list[VendorConfig], capability: str, **context) -> list[VendorConfig]:
        if not vendors:
            return []

        seed = context.get("seed")
        if seed is not None:
            # Deterministic mode for tests: use weighted random with seed
            return self._weighted_random(vendors, seed)

        # Smooth weighted round-robin
        return self._smooth_wrr(vendors, capability)

    def _smooth_wrr(self, vendors: list[VendorConfig], capability: str) -> list[VendorConfig]:
        """
        Smooth weighted round-robin: pick one winner per call,
        then return all vendors with the winner first.
        """
        cw = self._current_weights[capability]
        total_weight = sum(v.weight for v in vendors) or 1

        # Increase each vendor's current weight by its configured weight
        for v in vendors:
            cw[v.name] += v.weight

        # The vendor with the highest current weight wins this round
        winner = max(vendors, key=lambda v: cw[v.name])
        cw[winner.name] -= total_weight

        # Return winner first, then the rest in weight-descending order
        rest = [v for v in vendors if v.name != winner.name]
        rest.sort(key=lambda v: v.weight, reverse=True)
        return [winner] + rest

    @staticmethod
    def _weighted_random(vendors: list[VendorConfig], seed: int) -> list[VendorConfig]:
        """Deterministic weighted shuffle for tests."""
        rng = random.Random(seed)
        weighted = [(v, v.weight or 1) for v in vendors]
        result = []
        while weighted:
            total = sum(w for _, w in weighted)
            r = rng.uniform(0, total)
            cumulative = 0
            for i, (v, w) in enumerate(weighted):
                cumulative += w
                if r <= cumulative:
                    result.append(v)
                    weighted.pop(i)
                    break
        return result
