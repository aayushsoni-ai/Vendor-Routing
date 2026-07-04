"""
Vendor API endpoints — POST /vendors, GET /vendors.
"""

from typing import Optional

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
import httpx

from app.config import settings
from app.db.database import get_session
from app.models.vendor import VendorConfig, VendorResponse
from app.registry.registry import VendorRegistry

router = APIRouter(prefix="/vendors", tags=["Vendors"])


async def _notify_mock_register(config: VendorConfig):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.MOCK_VENDOR_BASE_URL}/mock/{config.name}/register",
                json={
                    "timeoutMs": config.timeout_ms,
                    "supportedFeatures": config.supported_features,
                    "rateLimitPerMinute": config.rate_limit_per_minute
                },
                timeout=1.0
            )
    except Exception as e:
        print(f"Error notifying mock register for {config.name}: {e}")


async def _notify_mock_delete(name: str):
    try:
        async with httpx.AsyncClient() as client:
            await client.delete(
                f"{settings.MOCK_VENDOR_BASE_URL}/mock/{name}",
                timeout=1.0
            )
    except Exception as e:
        print(f"Error notifying mock delete for {name}: {e}")


@router.post("", response_model=VendorResponse, status_code=201)
async def register_vendor(
    config: VendorConfig,
    session: AsyncSession = Depends(get_session),
) -> VendorResponse:
    """
    Register a new vendor with validated configuration.
    Returns 422 if the config fails validation, 409 if the name already exists.
    """
    registry = VendorRegistry(session)
    try:
        res = await registry.register(config)
        await _notify_mock_register(config)
        return res
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=list[VendorResponse])
async def list_vendors(
    capability: Optional[str] = Query(default=None, description="Filter by capability"),
    session: AsyncSession = Depends(get_session),
) -> list[VendorResponse]:
    """List all registered vendors, optionally filtered by capability."""
    registry = VendorRegistry(session)
    return await registry.list_vendors(capability=capability)


@router.delete("/{name}", status_code=204)
async def delete_vendor(
    name: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a vendor by name."""
    registry = VendorRegistry(session)
    deleted = await registry.delete_vendor(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Vendor '{name}' not found")
    await _notify_mock_delete(name)
    return None


@router.patch("/{name}", response_model=VendorResponse)
async def update_vendor(
    name: str,
    updates: dict,
    session: AsyncSession = Depends(get_session),
) -> VendorResponse:
    """Update specific parameters of an existing vendor."""
    registry = VendorRegistry(session)
    updated = await registry.update_vendor(name, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Vendor '{name}' not found")
    
    vendor_cfg = await registry.get_vendor_by_name(name)
    if vendor_cfg:
        await _notify_mock_register(vendor_cfg)
        
    return updated



