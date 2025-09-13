from __future__ import annotations

"""Utility helpers for the Mallsense SDK."""

import uuid
from typing import Mapping, MutableMapping


def generate_idempotency_key(prefix: str | None = None) -> str:
    """Return a unique Idempotency-Key string suitable for safe retries of writes.

    Optionally provide a prefix to help with debugging or grouping.
    """
    u = uuid.uuid4().hex
    return f"{prefix}-{u}" if prefix else u


def with_idempotency(headers: Mapping[str, str] | None = None, *, prefix: str | None = None) -> dict[str, str]:
    """Return a copy of headers with an Idempotency-Key set.

    Example:
        sdk.connectors.create("nifi", payload, headers=with_idempotency())
    """
    new: MutableMapping[str, str] = dict(headers or {})
    if "Idempotency-Key" not in new:
        new["Idempotency-Key"] = generate_idempotency_key(prefix)
    return dict(new)

