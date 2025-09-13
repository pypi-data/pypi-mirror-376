from __future__ import annotations

from typing import Any, Optional, Sequence

from ..http import HTTPApi
from ..models import Status2Tenant as Status2TenantModel, PatchedStatus2Tenant


class Status2TenantAPI:
    """Client for assigning statuses to tenants."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def list(
        self,
        *,
        assigned_from: Optional[str] = None,
        assigned_to: Optional[str] = None,
        created_from: Optional[str] = None,
        created_to: Optional[str] = None,
        project_location_ids: Optional[Sequence[int]] = None,
        tenant_ids: Optional[Sequence[int]] = None,
        updated_from: Optional[str] = None,
        updated_to: Optional[str] = None,
        user_ids: Optional[Sequence[int]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """List tenant status assignments with filtering and pagination."""
        params = {
            "assigned_from": assigned_from,
            "assigned_to": assigned_to,
            "created_from": created_from,
            "created_to": created_to,
            "project_location_ids": list(project_location_ids) if project_location_ids is not None else None,
            "tenant_ids": list(tenant_ids) if tenant_ids is not None else None,
            "updated_from": updated_from,
            "updated_to": updated_to,
            "user_ids": list(user_ids) if user_ids is not None else None,
            "limit": limit,
            "offset": offset,
        }
        return self._http.request("GET", "/api/status2tenant/", params=params)

    def create(self, payload: Status2TenantModel | dict) -> Any:
        """Create a tenant status assignment (strict payload validation)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("POST", "/api/status2tenant/", json_body=body)

    def update(self, status2tenant_id: int, payload: Status2TenantModel | dict) -> Any:
        """Replace a tenant status assignment (strict payload validation)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("PUT", f"/api/status2tenant/{status2tenant_id}/", json_body=body)

    def partial_update(self, status2tenant_id: int, payload: PatchedStatus2Tenant | dict) -> Any:
        """Patch a tenant status assignment (strict payload validation)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("PATCH", f"/api/status2tenant/{status2tenant_id}/", json_body=body)

    def delete(self, status2tenant_id: int) -> None:
        """Delete a tenant status assignment."""
        self._http.request("DELETE", f"/api/status2tenant/{status2tenant_id}/")

__all__ = ["Status2TenantAPI"]
"""Tenant status assignment client."""
