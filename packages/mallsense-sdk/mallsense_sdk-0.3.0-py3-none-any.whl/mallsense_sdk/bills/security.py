from __future__ import annotations

from typing import Any

from ..http import HTTPApi


class SecurityAPI:
    """Client for security/utility functions (e.g., filtration JWT)."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def create_l4l_filtration_jwt(self) -> Any:
        """Create a JWT token for downstream filtration services."""
        return self._http.request("POST", "/api/l4l-filtration-jwt/")

__all__ = ["SecurityAPI"]
"""Security utility client (filtration JWT, etc.)."""
