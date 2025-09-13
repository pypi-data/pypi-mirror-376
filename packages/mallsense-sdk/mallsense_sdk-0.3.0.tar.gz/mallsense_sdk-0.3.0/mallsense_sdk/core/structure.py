from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

import pandas as pd

from ..http import HTTPApi


STRUCTURE_TABLE_COLUMNS: Mapping[str, List[str]] = {
    "core/elements_admin_data_objects": [
        "pl_id",
        "id",
        "object_type",
        "marker",
        "name",
        "object_name",
        "is_active",
        "area_history",
        "external_ids",
        "object_params",
        "working_hours",
    ],
    "core/elements_ms_data_objects": [
        "pl_id",
        "object_type",
        "marker",
        "object_name",
        "area",
        "floor",
        "object_params",
        "date_from",
        "date_to",
    ],
    "core/elements_geo_objects": [
        "pl_id",
        "floor",
        "marker",
        "user_area",
        "object_type",
        "object_name",
        "marker",
        "date_to",
        "date_from",
        "polygon_area",
        "geo_coordinates",
        "plan_coordinates",
    ],
    "core/relations_dataobj2floor": [
        "pl_id",
        "object_type",
        "marker",
        "object_name",
        "floor",
        "date_from",
        "date_to",
    ],
    "core/relations_passway2dataobj": [
        "pl_id",
        "dataobj_type",
        "dataobj_marker",
        "passway_marker",
        "calc_sign",
        "date_from",
        "date_to",
    ],
    "core/relations_place2zone": [
        "pl_id",
        "place_marker",
        "floor",
        "date_from",
        "date_to",
        "group_marker",
        "group_name",
        "zone_marker",
        "zone_name",
        "content_percentage",
    ],
    "core/relations_tenant2floor": [
        "pl_id",
        "tenant_id",
        "tenant_marker",
        "tenant_name",
        "floor",
        "date_from",
        "date_to",
    ],
    "core/relations_tenant2location": [
        "pl_id",
        "tenant_id",
        "tenant_marker",
        "tenant_name",
        "date_from",
        "date_to",
    ],
    "core/relations_tenant2place": [
        "pl_id",
        "tenant_id",
        "tenant_marker",
        "tenant_name",
        "place_id",
        "place_marker",
        "place_name",
        "floor",
        "area",
        "date_from",
        "date_to",
    ],
    "core/relations_tenant2zone": [
        "pl_id",
        "tenant_id",
        "tenant_marker",
        "tenant_name",
        "group_marker",
        "group_name",
        "zone_marker",
        "zone_name",
        "floor",
        "content_percentage",
        "date_from",
        "date_to",
    ],
    "fpc/elements_pc_ipoints": [
        "pl_id",
        "marker",
        "line_count",
        "followed_by",
        "date_from",
        "date_to",
    ],
    "fpc/elements_pc_sensors": [
        "pl_id",
        "sensor_id",
        "sensor_type",
        "serial_number",
        "sensor_name",
        "username",
        "password",
        "ip",
        "port",
        "is_active",
    ],
    "fpc/relations_pcipoint2passway": [
        "pl_id",
        "passway_marker",
        "pc_ipoint_marker",
        "sensor_line_name",
        "timezone",
        "date_from",
        "date_to",
    ],
    "fpc/relations_sensor2dataobj": [
        "pl_id",
        "sensor_id",
        "sensor_type",
        "sensor_serial",
        "sensor_ip",
        "sensor_port",
        "sensor_line_name",
        "pcipoint_marker",
        "dataobj_type",
        "dataobj_marker",
        "calc_sign",
        "timezone",
        "date_from",
        "date_to",
    ],
    "fpc/relations_sensor2passway": [
        "pl_id",
        "sensor_id",
        "sensor_type",
        "sensor_serial",
        "sensor_ip",
        "sensor_port",
        "sensor_line_name",
        "pc_ipoint_marker",
        "passway_marker",
        "timezone",
        "date_from",
        "date_to",
    ],
    "fpc/relations_sensor2pcipoint": [
        "pl_id",
        "sensor_id",
        "sensor_type",
        "sensor_serial",
        "sensor_ip",
        "sensor_port",
        "pc_ipoint_marker",
        "date_from",
        "date_to",
    ],
}


class StructureAPI:
    """Client for Core Dashboard structure endpoints.

    Fetches project locations, available metrics list, and well‑typed structure tables.
    """

    _PL_STRUCTURE_URL_PATH = "/structure-service/v1/project_locations"
    _METRICS_LIST_URL_PATH = "/structure-service/v1/metrics-list"

    def __init__(self, http: HTTPApi):
        self._http = http

    def get_metrics_list(self) -> Any:
        """List available metrics defined for the Core service."""
        return self._http.request("GET", self._METRICS_LIST_URL_PATH)

    def get_pl_info(self, pl_id: Optional[int] = None) -> Any:
        """Get project locations or one by id.

        Parameters:
        - pl_id: Optional project location id. When None, returns the full list.
        """
        path = (
            self._PL_STRUCTURE_URL_PATH
            if pl_id is None
            else f"{self._PL_STRUCTURE_URL_PATH}/{pl_id}"
        )
        return self._http.request("GET", path)

    def get_structure_table(self, pl_id: int, structure_table: str) -> pd.DataFrame:
        """Fetch a structure table for a project location.

        Parameters:
        - pl_id: Project location id.
        - structure_table: One of keys from STRUCTURE_TABLE_COLUMNS.
        Returns a DataFrame with parsed dates where applicable.
        """
        if structure_table not in STRUCTURE_TABLE_COLUMNS:
            raise ValueError(f"Unknown table {structure_table}")
        path = f"{self._PL_STRUCTURE_URL_PATH}/{pl_id}/{structure_table}"
        response = self._http.request("GET", path)
        columns = STRUCTURE_TABLE_COLUMNS[structure_table]
        df = pd.DataFrame(response, columns=columns)
        if "date_from" in columns and not df.empty:
            df["date_from"] = pd.to_datetime(df["date_from"])  # type: ignore[assignment]
        if "date_to" in columns and not df.empty:
            df["date_to"] = pd.to_datetime(df["date_to"])  # type: ignore[assignment]
        return df

__all__ = ["StructureAPI", "STRUCTURE_TABLE_COLUMNS"]
