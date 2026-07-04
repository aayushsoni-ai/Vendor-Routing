"""
Vendor Registry — CRUD operations + capability lookup.

Backed by SQLite via SQLAlchemy. The registry is the source of truth
for which vendors are registered and what capabilities they serve.
"""

import json
from typing import Optional

# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import VendorRow
from app.models.vendor import VendorConfig, VendorResponse


class VendorRegistry:
    """Manages vendor registrations in the database."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def register(self, config: VendorConfig) -> VendorResponse:
        """
        Register a new vendor. Rejects duplicates by name.
        Returns the created vendor with its server-assigned id.
        """
        # Check for duplicate name
        existing = await self._session.execute(
            select(VendorRow).where(VendorRow.name == config.name)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Vendor '{config.name}' already exists")

        row = VendorRow(
            name=config.name,
            capability=config.capability,
            base_url=config.base_url,
            priority=config.priority,
            weight=config.weight,
            cost_per_request=config.cost_per_request,
            timeout_ms=config.timeout_ms,
            rate_limit_per_minute=config.rate_limit_per_minute,
            supported_features=json.dumps(config.supported_features),
            enabled=config.enabled,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._row_to_response(row)

    async def list_vendors(
        self, capability: Optional[str] = None
    ) -> list[VendorResponse]:
        """List all vendors, optionally filtered by capability."""
        stmt = select(VendorRow)
        if capability:
            stmt = stmt.where(VendorRow.capability == capability)
        stmt = stmt.order_by(VendorRow.priority)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._row_to_response(r) for r in rows]

    async def get_vendors_for_capability(
        self, capability: str
    ) -> list[VendorConfig]:
        """
        Get all vendor configs for a capability — used by the routing engine.
        Returns VendorConfig objects (not VendorResponse) so the engine
        can work with the validated config shape.
        """
        stmt = (
            select(VendorRow)
            .where(VendorRow.capability == capability)
            .order_by(VendorRow.priority)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._row_to_config(r) for r in rows]

    async def get_vendor_by_name(self, name: str) -> Optional[VendorConfig]:
        """Look up a single vendor by name."""
        result = await self._session.execute(
            select(VendorRow).where(VendorRow.name == name)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._row_to_config(row)

    async def update_vendor(self, name: str, updates: dict) -> Optional[VendorResponse]:
        """Update specific fields on an existing vendor."""
        result = await self._session.execute(
            select(VendorRow).where(VendorRow.name == name)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None

        for key, value in updates.items():
            if key == "supportedFeatures":
                setattr(row, "supported_features", json.dumps(value))
            elif key == "baseUrl":
                setattr(row, "base_url", value)
            elif key == "costPerRequest":
                setattr(row, "cost_per_request", value)
            elif key == "timeoutMs":
                setattr(row, "timeout_ms", value)
            elif key == "rateLimitPerMinute":
                setattr(row, "rate_limit_per_minute", value)
            elif hasattr(row, key):
                setattr(row, key, value)

        await self._session.commit()
        await self._session.refresh(row)
        return self._row_to_response(row)

    async def delete_vendor(self, name: str) -> bool:
        """Delete a vendor by name. Returns True if deleted, False if not found."""
        result = await self._session.execute(
            select(VendorRow).where(VendorRow.name == name)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True

    @staticmethod
    def _row_to_response(row: VendorRow) -> VendorResponse:
        return VendorResponse(
            id=row.id,
            name=row.name,
            capability=row.capability,
            baseUrl=row.base_url,
            priority=row.priority,
            weight=row.weight,
            costPerRequest=row.cost_per_request,
            timeoutMs=row.timeout_ms,
            rateLimitPerMinute=row.rate_limit_per_minute,
            supportedFeatures=json.loads(row.supported_features),
            enabled=row.enabled,
        )

    @staticmethod
    def _row_to_config(row: VendorRow) -> VendorConfig:
        return VendorConfig(
            name=row.name,
            capability=row.capability,
            baseUrl=row.base_url,
            priority=row.priority,
            weight=row.weight,
            costPerRequest=row.cost_per_request,
            timeoutMs=row.timeout_ms,
            rateLimitPerMinute=row.rate_limit_per_minute,
            supportedFeatures=json.loads(row.supported_features),
            enabled=row.enabled,
        )
