from __future__ import annotations

from typing import Any, Optional

from ..http import HTTPApi


class ResponsibilityZonesAPI:
    """Client for responsibility zones listings."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def list(self, *, limit: Optional[int] = None, offset: Optional[int] = None) -> Any:
        """List responsibility zones with pagination."""
        params = {"limit": limit, "offset": offset}
        return self._http.request("GET", "/api/responsibility-zone/", params=params)

__all__ = ["ResponsibilityZonesAPI"]
"""Responsibility zones client."""
