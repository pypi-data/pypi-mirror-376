from __future__ import annotations

from typing import Any, Optional, Sequence

from ..http import HTTPApi


class CorrectionsAPI:
    """Client for corrections endpoints (e.g., first bill date)."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def first_bill_date(self, *, project_location_ids: Sequence[int], tenant_ids: Optional[Sequence[int]] = None) -> Any:
        """Fetch the first bill date per location/tenant.

        Required: project_location_ids. Optional: tenant_ids.
        """
        params = {
            "project_location_ids": list(project_location_ids),
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
        }
        return self._http.request("GET", "/api/correction/first-bill-date/", params=params)

__all__ = ["CorrectionsAPI"]
"""Corrections client (e.g., first bill date)."""
