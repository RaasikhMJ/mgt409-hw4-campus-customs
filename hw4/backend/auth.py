"""Password hashing and signed session cookies.

The password itself is never stored. New accounts use PBKDF2-HMAC-SHA256,
a random salt, and 600,000 iterations. Seed accounts use the same algorithm
at 120,000 iterations, which is the count already in the database.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from pathlib import Path

NEW_ITERATIONS = 600_000
LEGACY_ITERATIONS = 120_000
SESSION_DAYS = 14
_KEY_FILE = Path(__file__).resolve().parent / ".session_key"


def hash_password(password: str, iterations: int = NEW_ITERATIONS) -> str:
    salt = secrets.token_urlsafe(12)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if not parts or parts[0] != "pbkdf2_sha256":
        return False
    if len(parts) == 4:
        _, rounds, salt, digest = parts
        try:
            iterations = int(rounds)
        except ValueError:
            return False
    elif len(parts) == 3:
        _, salt, digest = parts
        iterations = LEGACY_ITERATIONS
    else:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        iterations,
    ).hex()
    return hmac.compare_digest(check, digest)


# Hashed once so a missing account takes about as long as a real check.
DUMMY_HASH = hash_password("campus-customs-timing-pad")


def _secret() -> bytes:
    if _KEY_FILE.is_file():
        return _KEY_FILE.read_bytes().strip()
    _KEY_FILE.write_bytes(secrets.token_hex(32).encode())
    _KEY_FILE.chmod(0o600)
    return _KEY_FILE.read_bytes().strip()


def issue_session(user_id: int) -> str:
    expires = int(time.time()) + SESSION_DAYS * 24 * 3600
    body = f"{user_id}.{expires}"
    signature = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def read_session(token: str | None) -> int | None:
    if not token:
        return None
    user_id_s, dot, rest = token.partition(".")
    expires_s, dot2, signature = rest.partition(".")
    if not dot or not dot2 or not signature:
        return None
    body = f"{user_id_s}.{expires_s}"
    expected = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        user_id = int(user_id_s)
        expires = int(expires_s)
    except ValueError:
        return None
    if expires < time.time():
        return None
    return user_id
