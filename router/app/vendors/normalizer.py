"""
Response Normalizer — maps vendor-specific response shapes to canonical.

Each vendor returns its own raw JSON structure. The normalizer
converts it to the canonical shape per capability so the client
always sees the same response structure regardless of which vendor served them.

This is where the "return a standardized response regardless of vendor"
requirement is implemented.
"""


def normalize(capability: str, vendor_name: str, raw: dict) -> dict:
    """
    Normalize a vendor-specific response to the canonical shape.

    Args:
        capability: The capability being served (e.g. PAN_VERIFICATION)
        vendor_name: Which vendor produced this response
        raw: The raw JSON body from the vendor

    Returns:
        A dict in the canonical shape for the given capability
    """
    normalizer = _NORMALIZERS.get(capability)
    if normalizer is None:
        # Unknown capability — pass through the raw response with a warning.
        return raw
    return normalizer(vendor_name, raw)


def _normalize_pan_verification(vendor_name: str, raw: dict) -> dict:
    """
    Canonical PAN_VERIFICATION shape: { panStatus, nameMatch, dobMatch? }

    VendorA returns: { "verification": { "status": "valid", "name_matched": true } }
    VendorB returns: { "result": "VALID", "nameMatch": true }
    VendorC returns: { "data": { "pan_valid": true, "name_match": true } }
    """
    if vendor_name == "VendorA":
        verification = raw.get("verification", {})
        status_raw = verification.get("status", "").upper()
        return {
            "panStatus": status_raw if status_raw in ("VALID", "INVALID", "NOT_FOUND") else "UNKNOWN",
            "nameMatch": verification.get("name_matched"),
            "dobMatch": verification.get("dob_matched"),
        }
    elif vendor_name == "VendorB":
        result = raw.get("result", "").upper()
        return {
            "panStatus": result if result in ("VALID", "INVALID", "NOT_FOUND") else "UNKNOWN",
            "nameMatch": raw.get("nameMatch"),
        }
    elif vendor_name == "VendorC":
        data = raw.get("data", {})
        pan_valid = data.get("pan_valid", False)
        return {
            "panStatus": "VALID" if pan_valid else "INVALID",
            "nameMatch": data.get("name_match"),
        }
    else:
        # Unknown vendor for this capability — best-effort passthrough
        return {
            "panStatus": raw.get("panStatus", raw.get("result", raw.get("status", "UNKNOWN"))),
            "nameMatch": raw.get("nameMatch", raw.get("name_match", raw.get("name_matched"))),
        }


def _normalize_ocr(vendor_name: str, raw: dict) -> dict:
    """Canonical OCR shape — extensible placeholder."""
    return {
        "extractedText": raw.get("extractedText", raw.get("text", raw.get("data", {}).get("text", ""))),
        "confidence": raw.get("confidence", raw.get("data", {}).get("confidence")),
    }


def _normalize_sms(vendor_name: str, raw: dict) -> dict:
    """Canonical SMS shape — extensible placeholder."""
    return {
        "delivered": raw.get("delivered", raw.get("status") == "delivered"),
        "messageId": raw.get("messageId", raw.get("id")),
    }


_NORMALIZERS = {
    "PAN_VERIFICATION": _normalize_pan_verification,
    "OCR": _normalize_ocr,
    "SMS": _normalize_sms,
}
