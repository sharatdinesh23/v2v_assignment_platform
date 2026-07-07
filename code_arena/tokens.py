"""Short-lived signed tokens for the Excel export link.

The admin UI needs to hand the browser a URL it can GET to download results.
Rather than embedding the raw APP_SECRET in the page (which would leak it into
client HTML), we embed an HMAC token that is signed with the secret and expires
after a few minutes. The server verifies the signature + expiry; the secret
itself never leaves the backend.
"""
from __future__ import annotations

import base64
import hmac
import time
from hashlib import sha256

from .config import settings

# How long an export link stays valid (seconds).
TOKEN_TTL = 300


def _sign(expiry: int) -> str:
    msg = str(expiry).encode()
    digest = hmac.new(settings.app_secret.encode(), msg, sha256).hexdigest()
    return digest


def make_export_token(ttl: int = TOKEN_TTL) -> str:
    expiry = int(time.time()) + ttl
    raw = f"{expiry}:{_sign(expiry)}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def verify_export_token(token: str) -> bool:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        expiry_str, digest = raw.split(":", 1)
        expiry = int(expiry_str)
    except Exception:
        return False
    if expiry < int(time.time()):
        return False
    return hmac.compare_digest(digest, _sign(expiry))
