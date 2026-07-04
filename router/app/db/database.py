"""
Database engine and session factory.

Uses SQLAlchemy 2.0 async with aiosqlite for zero-infra persistence.
SQLite is chosen over Postgres to keep the project self-contained —
`docker-compose up` needs no external database, and the data volume
is small enough that SQLite's write-lock isn't a bottleneck.
"""

# pyrefly: ignore [missing-import]
import os
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Automatically create missing parent directories for SQLite databases to prevent "unable to open database file" errors
if settings.DATABASE_URL.startswith("sqlite"):
    db_path = settings.DATABASE_URL.split(":///")[-1]
    if db_path:
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # SQLite needs check_same_thread=False for async usage.
    connect_args={"check_same_thread": False},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables if they don't exist and auto-seed default vendors."""
    from app.db.tables import Base, VendorRow  # noqa: F811
    # pyrefly: ignore [missing-import]
    from sqlalchemy import select
    import json

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        async with session.begin():
            # Check if any vendors exist
            result = await session.execute(select(VendorRow).limit(1))
            if not result.scalar_one_or_none():
                # Seed default providers
                default_vendors = [
                    VendorRow(
                        name="VendorA",
                        capability="PAN_VERIFICATION",
                        base_url=settings.MOCK_VENDOR_BASE_URL,
                        priority=1,
                        weight=70,
                        cost_per_request=1.5,
                        timeout_ms=2000,
                        rate_limit_per_minute=100,
                        supported_features=json.dumps(["nameMatch", "dobMatch"]),
                        enabled=True
                    ),
                    VendorRow(
                        name="VendorB",
                        capability="PAN_VERIFICATION",
                        base_url=settings.MOCK_VENDOR_BASE_URL,
                        priority=2,
                        weight=30,
                        cost_per_request=1.2,
                        timeout_ms=3000,
                        rate_limit_per_minute=50,
                        supported_features=json.dumps(["nameMatch"]),
                        enabled=True
                    ),
                    VendorRow(
                        name="VendorC",
                        capability="PAN_VERIFICATION",
                        base_url=settings.MOCK_VENDOR_BASE_URL,
                        priority=3,
                        weight=0,
                        cost_per_request=1.0,
                        timeout_ms=2500,
                        rate_limit_per_minute=30,
                        supported_features=json.dumps(["nameMatch"]),
                        enabled=True
                    )
                ]
                session.add_all(default_vendors)
                await session.flush()


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency — yields a scoped async session."""
    async with async_session() as session:
        yield session
