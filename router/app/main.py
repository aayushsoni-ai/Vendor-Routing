"""
FastAPI application wiring.

This file does three things and nothing else:
1. Creates the FastAPI app with metadata for OpenAPI docs.
2. Registers lifespan events (DB init on startup).
3. Includes all API routers.
"""

from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize the database. Shutdown: nothing special needed for SQLite."""
    await init_db()
    # Sync existing DB vendors with the mock service on startup
    try:
        from app.db.database import async_session
        from app.registry.registry import VendorRegistry
        async with async_session() as session:
            registry = VendorRegistry(session)
            vendors = await registry.list_vendors()
            
            # pyrefly: ignore [missing-import]
            import httpx
            async with httpx.AsyncClient() as client:
                for vendor in vendors:
                    try:
                        await client.post(
                            f"{settings.MOCK_VENDOR_BASE_URL}/mock/{vendor.name}/register",
                            json={
                                "timeoutMs": vendor.timeout_ms,
                                "supportedFeatures": vendor.supported_features,
                                "rateLimitPerMinute": vendor.rate_limit_per_minute
                            },
                            timeout=1.0
                        )
                    except Exception as e:
                        print(f"Startup sync failed for {vendor.name}: {e}")
    except Exception as e:
        print(f"Startup sync failed entirely: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Intelligent Vendor Routing Platform — routes requests to the best "
        "available vendor using configurable strategies and live performance signals."
    ),
    lifespan=lifespan,
)

# CORS — allow the frontend dev server and any localhost origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register routers ---
from app.api.health import router as health_router  # noqa: E402
from app.api.vendors import router as vendors_router  # noqa: E402
from app.api.route import router as route_router  # noqa: E402
from app.api.metrics import router as metrics_router  # noqa: E402
from app.api.logs import router as logs_router  # noqa: E402
from app.api.agent import router as agent_router  # noqa: E402

app.include_router(health_router)
app.include_router(vendors_router)
app.include_router(route_router)
app.include_router(metrics_router)
app.include_router(logs_router)
app.include_router(agent_router)


