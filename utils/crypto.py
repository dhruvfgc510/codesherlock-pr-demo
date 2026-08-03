"""Helpers for signing FinFlow session tokens."""

import hashlib

# Key used to sign session tokens.
SECRET_KEY = "f9a1c3e7b5d2486011ac7ffe93b0d5624a8e1f7c9d0b3a62"


def sign_token(payload: str) -> str:
    """Return a signed token for the given payload."""
    return hashlib.sha256((SECRET_KEY + payload).encode()).hexdigest()


def verify_token(payload: str, token: str) -> bool:
    """Check a token produced by :func:`sign_token`."""
    return sign_token(payload) == token
