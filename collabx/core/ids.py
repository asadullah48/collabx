"""
Stable identifier helpers.

Python randomizes `str.__hash__` per process (PYTHONHASHSEED), so `hash(topic)`
produces a different value on every run. Editorial IDs are surfaced in the API
response and the dashboard, so they use a stable digest instead.
"""
import hashlib


def stable_suffix(text: str, modulo: int) -> int:
    """Deterministic non-negative integer < `modulo`, derived from `text`."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest, 16) % modulo
