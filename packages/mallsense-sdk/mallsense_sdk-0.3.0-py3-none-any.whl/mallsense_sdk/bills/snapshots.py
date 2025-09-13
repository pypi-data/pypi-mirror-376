from __future__ import annotations

from typing import Any, Optional, Sequence

from ..http import HTTPApi


class BillsSalesSnapshotsAPI:
    """Sales-like snapshot endpoints exposed under Bills API namespace.

    Uses `/api/snapshot*` paths from the Bills service.
    """

    def __init__(self, http: HTTPApi):
        self._http = http

    def get_snapshot_history(
        self,
        *,
        project_location_id: int,
        date_from: str,
        date_to: str,
        tenant_ids: Optional[Sequence[int]] = None,
        updated_from: Optional[str] = None,
        updated_to: Optional[str] = None,
    ) -> Any:
        params = {
            "project_location_id": project_location_id,
            "date_from": date_from,
            "date_to": date_to,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
            "updated_from": updated_from,
            "updated_to": updated_to,
        }
        return self._http.request("GET", "/api/snapshot-history/", params=params)

    def get_snapshot(
        self,
        *,
        project_location_id: int,
        date_from: str,
        date_to: str,
        actuality_time: Optional[str] = None,
        tenant_ids: Optional[Sequence[int]] = None,
        accept: str = "application/json",
    ) -> Any:
        params = {
            "project_location_id": project_location_id,
            "date_from": date_from,
            "date_to": date_to,
            "actuality_time": actuality_time,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
        }
        headers = {"Accept": accept}
        return self._http.request("GET", "/api/snapshot/", params=params, headers=headers)

    def get_snapshot_diff(
        self,
        *,
        project_location_id: int,
        date_from: str,
        date_to: str,
        actuality_time_from: str,
        actuality_time_to: str,
        tenant_ids: Optional[Sequence[int]] = None,
        accept: str = "application/json",
    ) -> Any:
        params = {
            "project_location_id": project_location_id,
            "date_from": date_from,
            "date_to": date_to,
            "actuality_time_from": actuality_time_from,
            "actuality_time_to": actuality_time_to,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
        }
        headers = {"Accept": accept}
        return self._http.request(
            "GET", "/api/snapshot-diff/", params=params, headers=headers
        )

    def get_snapshot_stream(
        self,
        *,
        project_location_id: int,
        date_from: str,
        date_to: str,
        actuality_time: Optional[str] = None,
        tenant_ids: Optional[Sequence[int]] = None,
        accept: str = "application/zip",
        chunk_size: int = 8192,
    ) -> Any:
        params = {
            "project_location_id": project_location_id,
            "date_from": date_from,
            "date_to": date_to,
            "actuality_time": actuality_time,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
        }
        headers = {"Accept": accept}
        return self._http.stream("GET", "/api/snapshot/", params=params, headers=headers, chunk_size=chunk_size)

    def get_snapshot_diff_stream(
        self,
        *,
        project_location_id: int,
        date_from: str,
        date_to: str,
        actuality_time_from: str,
        actuality_time_to: str,
        tenant_ids: Optional[Sequence[int]] = None,
        accept: str = "application/zip",
        chunk_size: int = 8192,
    ) -> Any:
        params = {
            "project_location_id": project_location_id,
            "date_from": date_from,
            "date_to": date_to,
            "actuality_time_from": actuality_time_from,
            "actuality_time_to": actuality_time_to,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
        }
        headers = {"Accept": accept}
        return self._http.stream("GET", "/api/snapshot-diff/", params=params, headers=headers, chunk_size=chunk_size)

__all__ = ["BillsSalesSnapshotsAPI"]
