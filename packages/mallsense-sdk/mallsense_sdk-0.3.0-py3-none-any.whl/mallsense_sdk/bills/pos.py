from __future__ import annotations

from typing import Any, Optional, Sequence

from ..http import HTTPApi
from ..models import PatchedPointOfSaleUpdate


class PointsOfSaleAPI:
    """Client for managing points of sale (POS)."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def list(
        self,
        *,
        connector_ids: Optional[Sequence[int]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        pos_date_from: Optional[str] = None,
        pos_date_to: Optional[str] = None,
        project_location_id: Optional[int] = None,
        project_location_ids: Optional[Sequence[int]] = None,
        tenant_id: Optional[int] = None,
        tenant_ids: Optional[Sequence[int]] = None,
        without_data: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """List points of sale with rich filtering and pagination."""
        params = {
            "connector_ids": list(connector_ids) if connector_ids is not None else None,
            "date_from": date_from,
            "date_to": date_to,
            "pos_date_from": pos_date_from,
            "pos_date_to": pos_date_to,
            "project_location_id": project_location_id,
            "project_location_ids": list(project_location_ids) if project_location_ids is not None else None,
            "tenant_id": tenant_id,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
            "without_data": without_data,
            "limit": limit,
            "offset": offset,
        }
        return self._http.request("GET", "/api/points-of-sale/", params=params)

    def partial_update(self, pos_id: int, payload: PatchedPointOfSaleUpdate | dict) -> Any:
        """Patch a POS entry (e.g., validity period)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("PATCH", f"/api/points-of-sale/{pos_id}/", json_body=body)

    def delete(self, pos_id: int) -> None:
        self._http.request("DELETE", f"/api/points-of-sale/{pos_id}/")

    def iter(self, **filters: Any):
        """Iterate over points of sale (auto-pagination)."""
        params = dict(filters)
        return self._http.paginate("/api/points-of-sale/", params=params)


class PointOfSaleBillHashAPI:
    """Client for POS bill hash listings."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def list(
        self,
        *,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        point_of_sale_ids: Optional[Sequence[int]] = None,
        tenant_ids: Optional[Sequence[int]] = None,
        updated_after: Optional[str] = None,
        updated_before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """List bill hashes for POS with optional time and tenant filters."""
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "point_of_sale_ids": list(point_of_sale_ids) if point_of_sale_ids is not None else None,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
            "updated_after": updated_after,
            "updated_before": updated_before,
            "limit": limit,
            "offset": offset,
        }
        return self._http.request("GET", "/api/point-of-sale-bill-hash/", params=params)

    def iter(self, **filters: Any):
        """Iterate over POS bill hash entries (auto-pagination)."""
        params = dict(filters)
        return self._http.paginate("/api/point-of-sale-bill-hash/", params=params)

__all__ = ["PointsOfSaleAPI", "PointOfSaleBillHashAPI"]
"""Points of sale client and POS bill hash listings."""
