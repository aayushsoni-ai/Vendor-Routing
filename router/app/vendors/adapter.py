"""
Vendor Adapter — calls a vendor over HTTP with per-call timeout.

Uses httpx async so timeouts and failover are real network events,
not faked. This is the Adapter pattern: each vendor has a different
external API, but the adapter presents a uniform interface to the
routing engine.
"""

import time

# pyrefly: ignore [missing-import]
import httpx

from app.exceptions import VendorError, VendorTimeoutError
from app.models.vendor import VendorConfig


class VendorAdapter:
    """
    Calls a vendor's HTTP endpoint with the configured timeout.
    Returns the raw response body as a dict for the normalizer to process.
    """

    def __init__(self):
        # Shared client with connection pooling. Timeout is set per-call
        # because each vendor has a different timeout config.
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))

    async def call(
        self,
        vendor: VendorConfig,
        capability: str,
        payload: dict,
    ) -> tuple[dict, int]:
        """
        Call the vendor and return (raw_response_body, latency_ms).

        Raises:
            VendorTimeoutError: if the call exceeds vendor.timeout_ms
            VendorError: if the vendor returns a non-2xx status
        """
        url = self._build_url(vendor.base_url, capability, vendor.name)
        timeout_seconds = vendor.timeout_ms / 1000.0

        start = time.monotonic()
        try:
            response = await self._client.post(
                url,
                json=payload,
                timeout=httpx.Timeout(timeout_seconds),
            )
        except httpx.TimeoutException:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            raise VendorTimeoutError(vendor.name, elapsed_ms)
        except httpx.ConnectError:
            raise VendorError(vendor.name, 503, "Connection refused")

        elapsed_ms = int((time.monotonic() - start) * 1000)

        if response.status_code >= 400:
            detail = response.text[:200] if response.text else ""
            raise VendorError(vendor.name, response.status_code, detail)

        return response.json(), elapsed_ms

    @staticmethod
    def _build_url(base_url: str, capability: str, vendor_name: str) -> str:
        """
        Build the vendor endpoint URL.
        Convention: mock vendors expose POST /<capability_path>/<vendor_name>
        e.g. http://mock-vendors:9000/pan/verify/VendorA
        """
        from app.config import settings

        # If the database contains a default local base URL, but a custom/production
        # base URL is configured in settings, use the configured one instead.
        if (
            base_url in ("http://mock-vendors:9000", "http://localhost:9000", "http://127.0.0.1:9000")
            and settings.MOCK_VENDOR_BASE_URL
            and settings.MOCK_VENDOR_BASE_URL != base_url
        ):
            base_url = settings.MOCK_VENDOR_BASE_URL

        capability_path = {
            "PAN_VERIFICATION": "/pan/verify",
            "OCR": "/ocr/extract",
            "SMS": "/sms/send",
        }.get(capability, f"/{capability.lower()}")

        return f"{base_url.rstrip('/')}{capability_path}/{vendor_name}"

    async def close(self):
        await self._client.aclose()


# Singleton adapter instance — shared across the app.
vendor_adapter = VendorAdapter()
