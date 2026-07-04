"""
GET /routing-logs — paginated routing decision logs with filters.
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_session
from app.db.tables import RoutingLogRow

router = APIRouter(tags=["Logs"])


@router.get("/routing-logs")
async def get_routing_logs(
    capability: Optional[str] = Query(default=None),
    vendor: Optional[str] = Query(default=None),
    outcome: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=None, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Query routing decision logs with filters and pagination.
    Each log captures the full routing story: filter reasons, strategy,
    attempts array (the failover chain), outcome, and timings.
    """
    effective_page_size = page_size or settings.LOG_PAGE_SIZE

    stmt = select(RoutingLogRow)

    if capability:
        stmt = stmt.where(RoutingLogRow.capability == capability)
    if vendor:
        stmt = stmt.where(RoutingLogRow.vendor_used == vendor)
    if outcome:
        stmt = stmt.where(RoutingLogRow.outcome == outcome)

    # Count total (for pagination metadata)
    from sqlalchemy import func

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    stmt = stmt.order_by(desc(RoutingLogRow.created_at))
    stmt = stmt.offset((page - 1) * effective_page_size).limit(effective_page_size)

    result = await session.execute(stmt)
    rows = result.scalars().all()

    logs = []
    for row in rows:
        logs.append(
            {
                "id": row.id,
                "requestId": row.request_id,
                "capability": row.capability,
                "strategyUsed": row.strategy_used,
                "vendorUsed": row.vendor_used,
                "outcome": row.outcome,
                "routingReason": row.routing_reason,
                "latencyMs": row.latency_ms,
                "cost": row.cost,
                "attempts": json.loads(row.attempts_json),
                "filterReasons": json.loads(row.filter_reasons_json),
                "createdAt": row.created_at.isoformat() if row.created_at else None,
            }
        )

    return {
        "logs": logs,
        "pagination": {
            "page": page,
            "pageSize": effective_page_size,
            "total": total,
            "totalPages": (total + effective_page_size - 1) // effective_page_size if total > 0 else 0,
        },
    }
