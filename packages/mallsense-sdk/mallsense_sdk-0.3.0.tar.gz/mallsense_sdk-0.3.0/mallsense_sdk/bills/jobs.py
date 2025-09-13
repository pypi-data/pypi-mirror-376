from __future__ import annotations

from typing import Any, Mapping

from ..http import HTTPApi
from ..models import TaskCreatorInput


class JobsAPI:
    """Client for creating and canceling background jobs on the Bills service."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def create(self, payload: TaskCreatorInput | Mapping[str, Any]) -> Any:
        """Create jobs for the specified scope (strict payload model)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("POST", "/api/task-creator/", json_body=body)

    def cancel(self, payload: TaskCreatorInput | Mapping[str, Any]) -> Any:
        """Cancel jobs matching the specified scope (strict payload model)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("POST", "/api/task-canceler/", json_body=body)

__all__ = ["JobsAPI"]
"""Jobs client for creating/canceling background tasks."""
