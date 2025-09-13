from __future__ import annotations

from typing import Any, Optional

from ..http import HTTPApi


class ProjectsAPI:
    """Client for listing project locations (Bills service view)."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def list(self, *, limit: Optional[int] = None, offset: Optional[int] = None) -> Any:
        """List project locations with pagination."""
        params = {"limit": limit, "offset": offset}
        return self._http.request("GET", "/api/project-locations/", params=params)

__all__ = ["ProjectsAPI"]
"""Projects client (Bills service view)."""
