"""
Health endpoint — service liveness plus a rollup of vendor health.
"""

import time

from fastapi import APIRouter

router = APIRouter(tags=["Health"])

_start_time = time.time()


@router.get("/health")
async def health_check() -> dict:
    """
    Liveness probe. Returns service status and uptime.
    Vendor health summary is added once the registry and health monitor exist.
    """
    uptime_seconds = round(time.time() - _start_time, 1)
    return {
        "status": "ok",
        "uptime_seconds": uptime_seconds,
        "version": "1.0.0",
    }
