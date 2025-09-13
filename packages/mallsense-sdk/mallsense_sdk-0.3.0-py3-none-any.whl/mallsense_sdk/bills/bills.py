from __future__ import annotations

from typing import Any, Optional, Sequence

from ..http import HTTPApi


class BillsAPI:
    """Bills data endpoints (list variants).

    Supports full, short, and simple representations with consistent filtering.
    """

    def __init__(self, http: HTTPApi):
        self._http = http

    def list_bills_full(
        self,
        *,
        date_from: str,
        date_to: str,
        bill_type: Optional[Sequence[str]] = None,
        connector_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        point_of_sale_ids: Optional[Sequence[int]] = None,
        tenant_ids: Optional[Sequence[int]] = None,
    ) -> Any:
        """List bills with full representation.

        Required: date_from, date_to (YYYY‑MM‑DD). Optional filters include bill_type,
        connector_type, point_of_sale_ids, tenant_ids, and pagination.
        """
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "bill_type": list(bill_type) if bill_type is not None else None,
            "connector_type": connector_type,
            "limit": limit,
            "offset": offset,
            "point_of_sale_ids": list(point_of_sale_ids) if point_of_sale_ids is not None else None,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
        }
        return self._http.request("GET", "/api/bills-full/", params=params)

    def list_bills_short(
        self,
        *,
        date_from: str,
        date_to: str,
        bill_type: Optional[Sequence[str]] = None,
        connector_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        point_of_sale_ids: Optional[Sequence[int]] = None,
        tenant_ids: Optional[Sequence[int]] = None,
    ) -> Any:
        """List bills with compact representation (short)."""
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "bill_type": list(bill_type) if bill_type is not None else None,
            "connector_type": connector_type,
            "limit": limit,
            "offset": offset,
            "point_of_sale_ids": list(point_of_sale_ids) if point_of_sale_ids is not None else None,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
        }
        return self._http.request("GET", "/api/bills-short/", params=params)

    def list_bills_simple(
        self,
        *,
        date_from: str,
        date_to: str,
        bill_type: Optional[Sequence[str]] = None,
        connector_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        point_of_sale_ids: Optional[Sequence[int]] = None,
        tenant_ids: Optional[Sequence[int]] = None,
    ) -> Any:
        """List bills with minimal representation (simple)."""
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "bill_type": list(bill_type) if bill_type is not None else None,
            "connector_type": connector_type,
            "limit": limit,
            "offset": offset,
            "point_of_sale_ids": list(point_of_sale_ids) if point_of_sale_ids is not None else None,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
        }
        return self._http.request("GET", "/api/bills-simple/", params=params)

    # Pagination helpers
    def iter_bills_full(self, **filters: Any):
        params = dict(filters)
        return self._http.paginate("/api/bills-full/", params=params)

    def iter_bills_short(self, **filters: Any):
        params = dict(filters)
        return self._http.paginate("/api/bills-short/", params=params)

    def iter_bills_simple(self, **filters: Any):
        params = dict(filters)
        return self._http.paginate("/api/bills-simple/", params=params)

__all__ = ["BillsAPI"]
"""Bills service client: list endpoints for bill data."""
