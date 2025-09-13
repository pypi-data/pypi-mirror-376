from __future__ import annotations

from typing import Any, Optional, Sequence

from ..http import HTTPApi
from ..models import TenantComment as TenantCommentModel, PatchedTenantComment


class TenantsAPI:
    """Client for tenants listing (Bills view)."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def list(
        self,
        *,
        project_location_id: Optional[int] = None,
        project_location_ids: Optional[Sequence[int]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """List tenants filtered by project location (pagination supported)."""
        params = {
            "project_location_id": project_location_id,
            "project_location_ids": list(project_location_ids) if project_location_ids is not None else None,
            "limit": limit,
            "offset": offset,
        }
        return self._http.request("GET", "/api/tenants/", params=params)


class TenantStatusAPI:
    """Client for tenant statuses."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def list(self, *, limit: Optional[int] = None, offset: Optional[int] = None) -> Any:
        """List tenant statuses (pagination supported)."""
        params = {"limit": limit, "offset": offset}
        return self._http.request("GET", "/api/tenant-status/", params=params)


class TenantCommentsAPI:
    """Client for tenant comments (list/create/update/patch)."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def list(
        self,
        *,
        assigned_from: Optional[str] = None,
        assigned_to: Optional[str] = None,
        comment_type: Optional[Sequence[str]] = None,
        project_location_ids: Optional[Sequence[int]] = None,
        responsibility_zone_ids: Optional[Sequence[int]] = None,
        tenant_ids: Optional[Sequence[int]] = None,
        user_ids: Optional[Sequence[int]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """List tenant comments using assignment/time filters (pagination supported)."""
        params = {
            "assigned_from": assigned_from,
            "assigned_to": assigned_to,
            "comment_type": list(comment_type) if comment_type is not None else None,
            "project_location_ids": list(project_location_ids) if project_location_ids is not None else None,
            "responsibility_zone_ids": list(responsibility_zone_ids) if responsibility_zone_ids is not None else None,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
            "user_ids": list(user_ids) if user_ids is not None else None,
            "limit": limit,
            "offset": offset,
        }
        return self._http.request("GET", "/api/tenant-comment/", params=params)

    def create(self, payload: TenantCommentModel | dict) -> Any:
        """Create a tenant comment (strict payload validation)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("POST", "/api/tenant-comment/", json_body=body)

    def update(self, comment_id: int, payload: TenantCommentModel | dict) -> Any:
        """Replace a tenant comment by id (strict payload validation)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("PUT", f"/api/tenant-comment/{comment_id}/", json_body=body)

    def partial_update(self, comment_id: int, payload: PatchedTenantComment | dict) -> Any:
        """Patch a tenant comment (strict payload validation)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("PATCH", f"/api/tenant-comment/{comment_id}/", json_body=body)

__all__ = ["TenantsAPI", "TenantStatusAPI", "TenantCommentsAPI"]
"""Tenants, tenant status, and tenant comments clients."""
