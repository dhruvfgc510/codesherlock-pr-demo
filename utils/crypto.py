"""Helpers for signing FinFlow session tokens."""

import hashlib
import hmac
import os
from typing import Optional

# Maximum payload size (bytes) accepted for signing, to bound CPU/memory use
# and reject abusive inputs before hashing.
MAX_PAYLOAD_SIZE = 4096

# HMAC-SHA256 hex digests are always 64 characters; anything else is invalid.
_TOKEN_LENGTH = 64

# The signing secret is loaded from the environment (or a secret manager) at use
# time — never hard-coded in source. The helpers fail fast if it is missing.
_SECRET_ENV_VAR = "FINFLOW_SECRET_KEY"


class TokenSigningError(Exception):
    """Raised when a token cannot be produced due to invalid or oversized input."""


def _get_secret() -> bytes:
    """Return the signing secret from the environment, or fail fast if unset.

    A missing secret is a deployment/configuration error, so it raises loudly
    rather than being treated as a routine verification failure.
    """
    secret = os.environ.get(_SECRET_ENV_VAR)
    if not secret:
        raise RuntimeError(
            f"Missing required {_SECRET_ENV_VAR} environment variable"
        )
    return secret.encode("utf-8")


def _ensure_payload_bytes(payload: str) -> bytes:
    """Validate ``payload`` and return its UTF-8 bytes.

    Raises TokenSigningError for non-string, unencodable, or oversized input.
    Error messages never include the secret or other internals.
    """
    if not isinstance(payload, str):
        raise TokenSigningError("payload must be a str")
    try:
        data = payload.encode("utf-8")
    except (AttributeError, UnicodeEncodeError) as exc:
        raise TokenSigningError("failed to encode payload") from exc
    if len(data) > MAX_PAYLOAD_SIZE:
        raise TokenSigningError("payload too large")
    return data


def sign_token(payload: str) -> str:
    """Return an HMAC-SHA256 hex digest binding ``payload`` to the secret key.

    Raises TokenSigningError on invalid or oversized input, and RuntimeError if
    no signing secret is configured.
    """
    data = _ensure_payload_bytes(payload)
    mac = hmac.new(_get_secret(), data, hashlib.sha256)
    return mac.hexdigest()


def verify_token(payload: Optional[str], token: Optional[str]) -> bool:
    """Check a token produced by :func:`sign_token`.

    Returns False for any invalid input or verification failure and never raises
    for routine input errors. A missing signing secret still fails fast, since
    that is a configuration error rather than attacker-supplied input.
    """
    if not isinstance(token, str) or len(token) != _TOKEN_LENGTH:
        return False
    try:
        expected = sign_token(payload)
    except TokenSigningError:
        # Invalid/oversized payloads are a verification failure, not an error
        # the caller must handle.
        return False
    # Constant-time comparison avoids leaking information via timing.
    return hmac.compare_digest(expected, token)
