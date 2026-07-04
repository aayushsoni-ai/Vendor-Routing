# Routing Decision Worked Examples

This document outlines standard routing behavior under various operational environments, including failover sequences and exclusions.

## Example 1: Healthy Priority-Based Routing
- **Configuration**:
  - `VendorA`: Priority 1, Cost ₹1.5, healthy.
  - `VendorB`: Priority 2, Cost ₹1.2, healthy.
- **Request**: `{ "capability": "PAN_VERIFICATION" }` (Strategy: `priority`)
- **Outcome**: Bypasses `VendorB` and routes directly to `VendorA`.
- **Telemetry log**:
  ```json
  {
    "status": "SUCCESS",
    "vendorUsed": "VendorA",
    "routingReason": "VendorA selected: highest priority (priority=1)",
    "attempts": [
      { "vendor": "VendorA", "outcome": "SUCCESS", "latencyMs": 420 }
    ]
  }
  ```

## Example 2: Outage & Automatic Failover
- **Scenario**: `VendorA` is experiencing an outage and times out.
- **Request**: `{ "capability": "PAN_VERIFICATION" }` (Strategy: `priority`)
- **Outcome**: The gateway attempts `VendorA`, times out after 2000ms, and automatically falls back to `VendorB`, returning a success response.
- **Telemetry log**:
  ```json
  {
    "status": "SUCCESS",
    "vendorUsed": "VendorB",
    "routingReason": "VendorB selected after failover (VendorA timed out (2005ms))",
    "attempts": [
      { "vendor": "VendorA", "outcome": "TIMEOUT", "latencyMs": 2005 },
      { "vendor": "VendorB", "outcome": "SUCCESS", "latencyMs": 850 }
    ]
  }
  ```

## Example 3: Feature-Based Hard Filter Exclusion
- **Scenario**: Caller requires the `dobMatch` feature. `VendorB` only supports `nameMatch`, while `VendorA` supports both.
- **Request**:
  ```json
  {
    "capability": "PAN_VERIFICATION",
    "requirements": {
      "requiredFeatures": ["dobMatch"]
    }
  }
  ```
- **Outcome**: `VendorB` is excluded during the filter phase. The request goes to `VendorA` directly regardless of priorities.
- **Telemetry log**:
  ```json
  {
    "status": "SUCCESS",
    "vendorUsed": "VendorA",
    "routingReason": "VendorA selected: highest priority. Excluded: VendorB (missing features: dobMatch)"
  }
  ```
