"""
Strategy ABC — base class for all routing strategies.

Strategy pattern: each routing strategy is a class implementing
the `rank` method that orders a list of candidate vendors.
The routing engine calls the active strategy after the filter pipeline.
"""

from abc import ABC, abstractmethod

from app.models.vendor import VendorConfig


class RoutingStrategy(ABC):
    """
    Abstract base class for routing strategies.

    A strategy takes a list of vendors that have already passed
    the filter pipeline and returns them in the order they should
    be attempted.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier matching the Strategy enum."""
        ...

    @abstractmethod
    def rank(
        self,
        vendors: list[VendorConfig],
        capability: str,
        **context,
    ) -> list[VendorConfig]:
        """
        Order the vendors for attempt execution.

        Args:
            vendors: Filtered candidate vendors
            capability: The capability being routed
            **context: Additional context (metrics, requirements, etc.)

        Returns:
            The same vendors in the order they should be tried
        """
        ...
