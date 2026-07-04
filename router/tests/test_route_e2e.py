# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
import pytest_asyncio
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.database import get_session, init_db
from app.db.tables import Base
from app.vendors.adapter import vendor_adapter

# Use an in-memory SQLite database for E2E tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(name="db_session")
async def db_session_fixture():
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async def override_get_session():
        async with async_session() as session:
            yield session
            
    app.dependency_overrides[get_session] = override_get_session
    
    async with async_session() as session:
        yield session
        
    app.dependency_overrides.clear()
    await engine.dispose()

@pytest.mark.asyncio
async def test_vendors_crud_and_routing(db_session, monkeypatch):
    client = TestClient(app)

    # 1. Register a vendor
    payload = {
        "name": "VendorA",
        "capability": "PAN_VERIFICATION",
        "baseUrl": "http://mock-vendor-a",
        "priority": 1,
        "weight": 70,
        "costPerRequest": 1.5,
        "timeoutMs": 2000,
        "rateLimitPerMinute": 100,
        "supportedFeatures": ["nameMatch", "dobMatch"],
        "enabled": True
    }
    response = client.post("/vendors", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "VendorA"
    assert data["id"] is not None

    # 2. Get list of vendors
    response = client.get("/vendors")
    assert response.status_code == 200
    vendors = response.json()
    assert len(vendors) == 1
    assert vendors[0]["name"] == "VendorA"

    # 3. Test Routing /route
    # Mock vendor_adapter.call to avoid actual network requests during testing
    async def mock_call(vendor, capability, payload):
        return {"verification": {"status": "valid", "name_matched": True}}, 120  # response, latency_ms

    monkeypatch.setattr(vendor_adapter, "call", mock_call)

    route_payload = {
        "capability": "PAN_VERIFICATION",
        "payload": {
            "pan": "ABCDE1234F",
            "name": "Rahul Sharma"
        },
        "requirements": {
            "maxLatencyMs": 2000
        }
    }
    
    response = client.post("/route", json=route_payload)
    assert response.status_code == 200
    route_data = response.json()
    assert route_data["status"] == "SUCCESS"
    assert route_data["vendorUsed"] == "VendorA"
    assert route_data["response"]["panStatus"] == "VALID"
    assert route_data["response"]["nameMatch"] is True

    # 4. Check routing logs
    response = client.get("/routing-logs")
    assert response.status_code == 200
    logs_data = response.json()
    assert len(logs_data["logs"]) == 1
    assert logs_data["logs"][0]["vendorUsed"] == "VendorA"
    assert logs_data["logs"][0]["outcome"] == "SUCCESS"

    request_id = route_data["requestId"]

    # 5. Check agent endpoints
    # Config from text
    response = client.post("/agent/config-from-text", json={"text": "Use health-based routing with failover"})
    assert response.status_code == 200
    assert "config" in response.json()
    assert response.json()["config"]["strategy"] == "health_based"

    # Explain decision
    response = client.post("/agent/explain-decision", json={"requestId": request_id})
    assert response.status_code == 200
    assert "explanation" in response.json()

    # Detect unhealthy
    response = client.get("/agent/detect-unhealthy")
    assert response.status_code == 200
    assert "issues" in response.json()

    # Recommend strategy
    response = client.post("/agent/recommend-strategy", json={"goal": "Minimize latency"})
    assert response.status_code == 200
    assert "recommendation" in response.json()

    # 6. Delete the vendor
    response = client.delete("/vendors/VendorA")
    assert response.status_code == 204

    # Verify deleted
    response = client.get("/vendors")
    assert response.status_code == 200
    assert len(response.json()) == 0


