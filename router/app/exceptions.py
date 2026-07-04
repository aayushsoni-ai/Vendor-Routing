"""
Custom exceptions for the routing platform.

Named, typed exceptions — not generic RuntimeErrors. Each one
carries context so API handlers can build specific 4xx/5xx responses.
"""


class VendorRoutingError(Exception):
    """Base exception for all vendor routing errors."""

    pass


class VendorTimeoutError(VendorRoutingError):
    """Raised when a vendor call exceeds its configured timeout."""

    def __init__(self, vendor_name: str, timeout_ms: int):
        self.vendor_name = vendor_name
        self.timeout_ms = timeout_ms
        super().__init__(f"{vendor_name} timed out after {timeout_ms}ms")


class VendorError(VendorRoutingError):
    """Raised when a vendor returns a non-2xx response."""

    def __init__(self, vendor_name: str, status_code: int, detail: str = ""):
        self.vendor_name = vendor_name
        self.status_code = status_code
        self.kind = self._classify(status_code)
        self.detail = detail
        super().__init__(
            f"{vendor_name} returned {status_code}: {self.kind} — {detail}"
        )

    @staticmethod
    def _classify(status_code: int) -> str:
        if status_code == 429:
            return "RATE_LIMITED"
        if status_code == 422:
            return "UNSUPPORTED_FEATURE"
        if 500 <= status_code < 600:
            return "ERROR_5XX"
        return f"ERROR_{status_code}"


class NoHealthyVendorError(VendorRoutingError):
    """Raised when no vendor survives the filter pipeline."""

    def __init__(self, capability: str, reasons: dict[str, str]):
        self.capability = capability
        self.reasons = reasons
        super().__init__(
            f"No healthy vendor for {capability}: {reasons}"
        )


class RateLimitExceededError(VendorRoutingError):
    """Raised when the router's own rate limiter blocks a vendor call."""

    def __init__(self, vendor_name: str):
        self.vendor_name = vendor_name
        super().__init__(f"Rate limit exceeded for {vendor_name}")
