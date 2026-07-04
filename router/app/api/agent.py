"""
Agent API Router — exposes Claude-powered operations.

Includes config parsing, decision explanation, log anomaly detection, and strategies.
"""

import json
from typing import Optional
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.tables import RoutingLogRow, VendorRow
from app.agent.service import agent_service
from app.api.metrics import get_vendor_metrics

router = APIRouter(prefix="/agent", tags=["Agentic AI"])


class TextPayload(BaseModel):
    text: str


class RequestIdPayload(BaseModel):
    requestId: str


class GoalPayload(BaseModel):
    goal: str


@router.post("/config-from-text")
async def config_from_text(payload: TextPayload):
    """
    Parse a plain English description of routing preferences and return
    a validated routing configuration.
    """
    try:
        config = await agent_service.generate_config_from_text(payload.text)
        return {"config": config, "mode": "mock" if agent_service.is_mock_mode else "live"}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/explain-decision")
async def explain_decision(
    payload: RequestIdPayload,
    session: AsyncSession = Depends(get_session),
):
    """
    Given a requestId, fetch the routing decision log from the database
    and ask Claude to explain why that decision was made.
    """
    stmt = select(RoutingLogRow).where(RoutingLogRow.request_id == payload.requestId)
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Routing log entry not found")

    log_entry = {
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
    }

    explanation = await agent_service.explain_decision(log_entry)
    return {"explanation": explanation, "mode": "mock" if agent_service.is_mock_mode else "live"}


@router.get("/detect-unhealthy")
async def detect_unhealthy(
    session: AsyncSession = Depends(get_session),
):
    """
    Read current metrics and recent logs to diagnose degraded or unhealthy vendors.
    """
    # Fetch live metrics
    metrics = await get_vendor_metrics()

    # Fetch recent routing logs (last 20)
    stmt = select(RoutingLogRow).order_by(RoutingLogRow.created_at.desc()).limit(20)
    result = await session.execute(stmt)
    rows = result.scalars().all()
    logs = []
    for row in rows:
        logs.append({
            "vendorUsed": row.vendor_used,
            "outcome": row.outcome,
            "latencyMs": row.latency_ms,
            "routingReason": row.routing_reason,
        })

    issues = await agent_service.detect_unhealthy_vendors(metrics, logs)
    return {"issues": issues, "mode": "mock" if agent_service.is_mock_mode else "live"}


@router.post("/recommend-strategy")
async def recommend_strategy(payload: GoalPayload):
    """
    Recommend a routing strategy and fallback sequence based on operational goals
    and current metrics.
    """
    metrics = await get_vendor_metrics()
    recommendation = await agent_service.recommend_strategy(payload.goal, metrics)
    return {"recommendation": recommendation, "mode": "mock" if agent_service.is_mock_mode else "live"}
