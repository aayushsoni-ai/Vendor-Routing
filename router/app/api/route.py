"""
POST /route — the unified routing entrypoint.

This is the most important endpoint: it validates the request,
pulls vendors, runs the routing engine, and returns a standardized response.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.models.routing import RouteRequest
from app.registry.registry import VendorRegistry
from app.routing.engine import route_request

router = APIRouter(tags=["Routing"])


@router.post("/route")
async def route(
    request: RouteRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Route a request to the best available vendor.

    The client sends a capability + payload + optional requirements.
    The engine filters, ranks, and attempts vendors with automatic failover.
    Returns a standardized response with the routing decision story.
    """
    registry = VendorRegistry(session)
    vendors = await registry.get_vendors_for_capability(request.capability)

    if not vendors:
        raise HTTPException(
            status_code=404,
            detail=f"No vendors registered for capability: {request.capability}",
        )

    # Determine strategy from routing config (could be per-capability in the future)
    # For now, use the request's strategy override or default
    strategy_name = None
    if request.requirements and request.requirements.strategy:
        strategy_name = request.requirements.strategy.value

    result = await route_request(
        request=request,
        vendors=vendors,
        session=session,
        strategy_name=strategy_name,
        failover_enabled=True,
    )

    return result
