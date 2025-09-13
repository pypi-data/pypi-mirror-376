from __future__ import annotations

import re
from typing import Any, Mapping, Optional, Sequence, Dict, Type

from ..http import HTTPApi
from .. import models
from pydantic import BaseModel


class ConnectorsAPI:
    """Connectors management client.

    Provides discovery and CRUD operations for all connector types exposed under
    `/api/manage-connectors/{type}/`. Payloads are validated against strict models.
    """

    def __init__(self, http: HTTPApi):
        self._http = http

    def list_types(self) -> Any:
        """List available connector types configured on the server."""
        return self._http.request("GET", "/api/manage-connectors/connector-types/")

    def list_connectors(
        self,
        *,
        connector_types: Optional[Sequence[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        project_location_id: Optional[int] = None,
        project_location_ids: Optional[Sequence[int]] = None,
        tenant_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Any:
        """Aggregated connectors listing across types.

        Filters include connector types, date range, locations, tenant, and pagination.
        """
        params = {
            "connector_types": list(connector_types) if connector_types is not None else None,
            "date_from": date_from,
            "date_to": date_to,
            "project_location_id": project_location_id,
            "project_location_ids": list(project_location_ids) if project_location_ids is not None else None,
            "tenant_id": tenant_id,
            "limit": limit,
            "offset": offset,
        }
        return self._http.request("GET", "/api/connectors/", params=params)

    def iter_connectors(self, **filters: Any):
        params = dict(filters)
        return self._http.paginate("/api/connectors/", params=params)

    def list(self, connector_type: str, *, limit: Optional[int] = None, offset: Optional[int] = None) -> Any:
        """List connectors of a specific type."""
        params = {"limit": limit, "offset": offset}
        return self._http.request("GET", f"/api/manage-connectors/{connector_type}/", params=params)

    def _to_pascal(self, name: str) -> str:
        parts = [p for p in re.split(r"[^a-zA-Z0-9]+", name) if p]
        return "".join(p[:1].upper() + p[1:] for p in parts)

    def _validate_payload(self, connector_type: str, payload: Any, *, for_patch: bool = False) -> Dict[str, Any]:
        if isinstance(payload, BaseModel):
            return payload.model_dump(exclude_none=True)
        schema_key = f"{connector_type}_serializer"
        schema_name = f"Patched{schema_key}" if for_patch else schema_key
        class_name = self._to_pascal(schema_name)
        model_cls: Type[BaseModel] = getattr(models, class_name)
        return model_cls(**payload).model_dump(exclude_none=True)

    def create(
        self,
        connector_type: str,
        payload: Mapping[str, Any] | BaseModel,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        """Create a connector instance of the given type.

        `payload` may be a dict or a strict Pydantic model (e.g., `NifiSerializer`).
        """
        body = self._validate_payload(connector_type, payload, for_patch=False)
        return self._http.request(
            "POST", f"/api/manage-connectors/{connector_type}/", json_body=body, headers=headers
        )

    def retrieve(self, connector_type: str, connector_id: int) -> Any:
        """Retrieve a connector by id."""
        return self._http.request("GET", f"/api/manage-connectors/{connector_type}/{connector_id}/")

    def update(
        self,
        connector_type: str,
        connector_id: int,
        payload: Mapping[str, Any] | BaseModel,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        """Update a connector, validating against the strict model."""
        body = self._validate_payload(connector_type, payload, for_patch=False)
        return self._http.request(
            "PUT",
            f"/api/manage-connectors/{connector_type}/{connector_id}/",
            json_body=body,
            headers=headers,
        )

    def partial_update(
        self,
        connector_type: str,
        connector_id: int,
        payload: Mapping[str, Any] | BaseModel,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        """Patch a connector using a `Patched{Type}Serializer` model."""
        body = self._validate_payload(connector_type, payload, for_patch=True)
        return self._http.request(
            "PATCH",
            f"/api/manage-connectors/{connector_type}/{connector_id}/",
            json_body=body,
            headers=headers,
        )

    def delete(self, connector_type: str, connector_id: int) -> None:
        """Delete a connector by id."""
        self._http.request("DELETE", f"/api/manage-connectors/{connector_type}/{connector_id}/")


class CashierModuleExtensionsAPI:
    """Cashier Module Extensions client under `/api/cashier-module/extensions/`."""

    def __init__(self, http: HTTPApi):
        self._http = http

    def list(self, *, limit: Optional[int] = None, offset: Optional[int] = None) -> Any:
        """List extensions with pagination."""
        params = {"limit": limit, "offset": offset}
        return self._http.request("GET", "/api/cashier-module/extensions/", params=params)

    def create(self, payload: models.Extension | Mapping[str, Any]) -> Any:
        """Create a new extension (strict payload validation)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("POST", "/api/cashier-module/extensions/", json_body=body)

    def retrieve(self, extension_id: int) -> Any:
        """Retrieve an extension by id."""
        return self._http.request("GET", f"/api/cashier-module/extensions/{extension_id}/")

    def update(self, extension_id: int, payload: models.Extension | Mapping[str, Any]) -> Any:
        """Replace an extension (strict payload validation)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("PUT", f"/api/cashier-module/extensions/{extension_id}/", json_body=body)

    def partial_update(self, extension_id: int, payload: models.PatchedExtension | Mapping[str, Any]) -> Any:
        """Patch an extension (strict payload validation)."""
        body = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self._http.request("PATCH", f"/api/cashier-module/extensions/{extension_id}/", json_body=body)

    def delete(self, extension_id: int) -> None:
        """Delete an extension by id."""
        self._http.request("DELETE", f"/api/cashier-module/extensions/{extension_id}/")

__all__ = ["ConnectorsAPI", "CashierModuleExtensionsAPI"]
"""Connectors management client and cashier-module extensions client."""
