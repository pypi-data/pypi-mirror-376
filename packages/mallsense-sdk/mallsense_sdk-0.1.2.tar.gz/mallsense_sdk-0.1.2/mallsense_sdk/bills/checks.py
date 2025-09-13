from __future__ import annotations

from typing import Any, Mapping

from ..http import HTTPApi
from ..models import CheckResultStatusUpdate, PatchedCheckResultStatusUpdate


class ChecksAPI:
    """Client for data quality check results.

    Supports listing summary/detail and updating check statuses with strict payloads.
    """

    def __init__(self, http: HTTPApi):
        self._http = http

    def get_check_result(self) -> Any:
        """Retrieve summary of check results from the database."""
        return self._http.request("GET", "/api/check-result/")

    def get_check_result_detail(self) -> Any:
        """Trigger a detailed check run and retrieve its result."""
        return self._http.request("GET", "/api/check-result-detail/")

    def update_check_result_status(self, check_result_id: int, payload: CheckResultStatusUpdate | Mapping[str, Any]) -> Any:
        """Update a check result status (PUT) with a strict payload model."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("PUT", f"/api/check-result-status-update/{check_result_id}/", json_body=body)

    def partial_update_check_result_status(self, check_result_id: int, payload: PatchedCheckResultStatusUpdate | Mapping[str, Any]) -> Any:
        """Patch a check result status (PATCH) with a strict payload model."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("PATCH", f"/api/check-result-status-update/{check_result_id}/", json_body=body)

__all__ = ["ChecksAPI"]
"""Checks client for data quality results and status updates."""
