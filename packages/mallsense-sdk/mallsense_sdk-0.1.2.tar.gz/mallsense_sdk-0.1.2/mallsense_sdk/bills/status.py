from __future__ import annotations

from typing import Any, Optional, Sequence

from ..http import HTTPApi
from ..models import StatusPointOfSaleManualCreate


class StatusAPI:
    """Client for point‑of‑sale statuses (auto and manual)."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def list_point_of_sale_auto(
        self,
        *,
        date_from: str,
        date_to: str,
        project_location_ids: Sequence[int],
        is_latest_status: Optional[bool] = None,
        status: Optional[Sequence[str]] = None,
        point_of_sale_ids: Optional[Sequence[int]] = None,
        tenant_ids: Optional[Sequence[int]] = None,
        updated_from: Optional[str] = None,
        updated_to: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """List auto‑computed POS statuses for the given date range and locations."""
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "project_location_ids": list(project_location_ids),
            "is_latest_status": is_latest_status,
            "status": list(status) if status is not None else None,
            "point_of_sale_ids": list(point_of_sale_ids) if point_of_sale_ids is not None else None,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
            "updated_from": updated_from,
            "updated_to": updated_to,
            "limit": limit,
            "offset": offset,
        }
        return self._http.request("GET", "/api/status-point-of-sale-auto/", params=params)

    def list_point_of_sale_manual(
        self,
        *,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        project_location_ids: Optional[Sequence[int]] = None,
        status: Optional[Sequence[str]] = None,
        point_of_sale_ids: Optional[Sequence[int]] = None,
        tenant_ids: Optional[Sequence[int]] = None,
        updated_from: Optional[str] = None,
        updated_to: Optional[str] = None,
        user_ids: Optional[Sequence[int]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """List manually set POS statuses with rich filtering and pagination."""
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "project_location_ids": list(project_location_ids) if project_location_ids is not None else None,
            "status": list(status) if status is not None else None,
            "point_of_sale_ids": list(point_of_sale_ids) if point_of_sale_ids is not None else None,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
            "updated_from": updated_from,
            "updated_to": updated_to,
            "user_ids": list(user_ids) if user_ids is not None else None,
            "limit": limit,
            "offset": offset,
        }
        return self._http.request("GET", "/api/status-point-of-sale-manual/", params=params)

    def create_point_of_sale_manual(self, payload: StatusPointOfSaleManualCreate | dict) -> Any:
        """Create a manual POS status entry (strict payload validation)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("POST", "/api/status-point-of-sale-manual/", json_body=body)

__all__ = ["StatusAPI"]
"""Status (auto/manual) client for points of sale."""
