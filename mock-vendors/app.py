"""
Mock Vendor Service — standalone FastAPI app simulating real third-party vendors.

Each vendor is driven by a profile in vendor_profiles.json and behaves
realistically: variable latency, random errors, rate limiting, and
vendor-specific response shapes. This makes failover, timeouts, and
rate-limit handling *genuine* HTTP events, not faked.

A control switch (POST /mock/{vendor}/toggle-down) lets you force a
vendor down live during a demo — the money feature for showing failover.
"""

import asyncio
import json
import random
import re
import time
from pathlib import Path
from collections import defaultdict

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException, Request
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mock Vendor Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load vendor profiles
_profiles_path = Path(__file__).parent / "vendor_profiles.json"
with open(_profiles_path) as f:
    VENDOR_PROFILES = json.load(f)

# Runtime state: tracks which vendors are forced down and per-minute request counts
_forced_down: dict[str, bool] = {}
_request_counts: dict[str, list[float]] = defaultdict(list)  # vendor → list of timestamps


def _is_rate_limited(vendor_name: str, limit: int) -> bool:
    """Check if vendor has exceeded its per-minute rate limit."""
    now = time.time()
    window_start = now - 60
    timestamps = _request_counts[vendor_name]
    # Prune old entries
    _request_counts[vendor_name] = [t for t in timestamps if t > window_start]
    return len(_request_counts[vendor_name]) >= limit


def _record_request(vendor_name: str):
    _request_counts[vendor_name].append(time.time())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mock-vendors", "vendors": list(VENDOR_PROFILES.keys())}


@app.get("/mock/status")
async def vendor_status():
    """Show the current state of all mock vendors."""
    status = {}
    for name, profile in VENDOR_PROFILES.items():
        status[name] = {
            "profile": profile,
            "forcedDown": _forced_down.get(name, False),
            "requestsInWindow": len(_request_counts.get(name, [])),
        }
    return status


@app.post("/mock/{vendor_name}/toggle-down")
async def toggle_vendor_down(vendor_name: str):
    """Force a vendor down (or back up) — the live demo control switch."""
    current = _forced_down.get(vendor_name, False)
    _forced_down[vendor_name] = not current
    new_state = "DOWN" if not current else "UP"
    return {"vendor": vendor_name, "state": new_state}


@app.post("/mock/{vendor_name}/set-state")
async def set_vendor_state(vendor_name: str, request: Request):
    """Set vendor state explicitly."""
    body = await request.json()
    if "down" in body:
        _forced_down[vendor_name] = body["down"]
    return {"vendor": vendor_name, "forcedDown": _forced_down.get(vendor_name, False)}


@app.post("/mock/{vendor_name}/register")
async def register_mock_profile(vendor_name: str, request: Request):
    """Dynamically register or update a vendor profile in the mock service."""
    body = await request.json()
    VENDOR_PROFILES[vendor_name] = {
        "baseLatencyMs": min(200, max(50, body.get("timeoutMs", 2000) // 10)),
        "jitterMs": 20,
        "errorRate": 0.05,
        "supports": body.get("supportedFeatures", ["nameMatch"]),
        "rateLimitPerMinute": body.get("rateLimitPerMinute", 100)
    }
    return {"status": "registered", "profile": VENDOR_PROFILES[vendor_name]}


@app.delete("/mock/{vendor_name}")
async def delete_mock_profile(vendor_name: str):
    """Dynamically delete a vendor profile from the mock service."""
    if vendor_name in VENDOR_PROFILES:
        del VENDOR_PROFILES[vendor_name]
    if vendor_name in _forced_down:
        del _forced_down[vendor_name]
    return {"status": "deleted"}


# --- PAN Verification endpoints (vendor-specific response shapes) ---

@app.post("/pan/verify/{vendor_name}")
async def pan_verify(vendor_name: str, request: Request):
    """
    Simulate PAN verification for a specific vendor.
    Each vendor returns a different response shape — the normalizer
    in the router service maps these to the canonical shape.
    """
    profile = VENDOR_PROFILES.get(vendor_name)
    if profile is None:
        profile = {
            "baseLatencyMs": 150,
            "jitterMs": 20,
            "errorRate": 0.05,
            "supports": ["nameMatch"],
            "rateLimitPerMinute": 100
        }
        VENDOR_PROFILES[vendor_name] = profile

    # Check forced-down state
    if _forced_down.get(vendor_name, False):
        raise HTTPException(status_code=503, detail=f"{vendor_name} is down (forced)")

    # Check rate limit
    if _is_rate_limited(vendor_name, profile["rateLimitPerMinute"]):
        raise HTTPException(status_code=429, detail=f"{vendor_name} rate limit exceeded")
    _record_request(vendor_name)

    body = await request.json()

    # Check required features
    required_features = body.get("requiredFeatures", [])
    for feature in required_features:
        if feature not in profile["supports"]:
            raise HTTPException(
                status_code=422,
                detail=f"{vendor_name} does not support feature: {feature}",
            )

    # Simulate latency (base ± jitter)
    latency_ms = profile["baseLatencyMs"] + random.randint(
        -profile["jitterMs"], profile["jitterMs"]
    )
    latency_ms = max(50, latency_ms)  # Floor at 50ms
    await asyncio.sleep(latency_ms / 1000.0)

    # Simulate random errors
    if random.random() < profile["errorRate"]:
        raise HTTPException(status_code=500, detail=f"{vendor_name} internal error (simulated)")

    # Validate PAN format
    pan = body.get("pan", "")
    pan_valid = bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan))
    name = body.get("name", "")
    # Simple name match: check if the name is non-empty
    name_matched = bool(name and len(name) > 1)

    # Return vendor-specific response shapes
    if vendor_name == "VendorA":
        return {
            "verification": {
                "status": "valid" if pan_valid else "invalid",
                "name_matched": name_matched,
                "dob_matched": True,  # VendorA supports dobMatch
            }
        }
    elif vendor_name == "VendorB":
        return {
            "result": "VALID" if pan_valid else "INVALID",
            "nameMatch": name_matched,
        }
    elif vendor_name == "VendorC":
        return {
            "data": {
                "pan_valid": pan_valid,
                "name_match": name_matched,
            }
        }
    else:
        return {
            "panStatus": "VALID" if pan_valid else "INVALID",
            "nameMatch": name_matched,
        }


# --- OCR endpoints (placeholder for extensibility) ---

@app.post("/ocr/extract/{vendor_name}")
async def ocr_extract(vendor_name: str, request: Request):
    """Simulate OCR extraction."""
    profile = VENDOR_PROFILES.get(vendor_name)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Unknown vendor: {vendor_name}")
    if _forced_down.get(vendor_name, False):
        raise HTTPException(status_code=503, detail=f"{vendor_name} is down")

    await asyncio.sleep(profile["baseLatencyMs"] / 1000.0)
    return {"extractedText": "Sample extracted text", "confidence": 0.95}


# --- SMS endpoints (placeholder for extensibility) ---

@app.post("/sms/send/{vendor_name}")
async def sms_send(vendor_name: str, request: Request):
    """Simulate SMS sending."""
    profile = VENDOR_PROFILES.get(vendor_name)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Unknown vendor: {vendor_name}")
    if _forced_down.get(vendor_name, False):
        raise HTTPException(status_code=503, detail=f"{vendor_name} is down")

    await asyncio.sleep(profile["baseLatencyMs"] / 1000.0)
    return {"status": "delivered", "messageId": f"msg-{random.randint(1000, 9999)}"}
