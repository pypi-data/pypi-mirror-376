from __future__ import annotations

from typing import Any

from ..http import HTTPApi


class ConnectorTasksAPI:
    """Client for connector tasks.

    Supports listing connector tasks with rich filtering and retrieving by id.
    """

    def __init__(self, http: HTTPApi):
        self._http = http

    def list(self, **filters: Any) -> Any:
        """List tasks with arbitrary filters.

        Array filters are encoded as CSV automatically by the HTTP client.
        """
        return self._http.request("GET", "/api/connector-task/", params=filters)

    def retrieve(self, task_id: int) -> Any:
        """Retrieve a task by id."""
        return self._http.request("GET", f"/api/connector-task/{task_id}/")

__all__ = ["ConnectorTasksAPI"]
"""Connector tasks client."""
