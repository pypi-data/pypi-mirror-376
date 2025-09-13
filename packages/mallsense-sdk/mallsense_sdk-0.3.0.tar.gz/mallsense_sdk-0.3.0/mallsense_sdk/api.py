from __future__ import annotations

"""Unified client for the Mallsense platform.

This module exposes `MallsenseSDK`, a high‑level entry point that wires together
Core (Dashboard), Sales, and Bills service clients with consistent configuration
and authentication.
"""

import json
import os
from typing import Optional

from .http import HTTPApi
from .core import MetricsAPI, StructureAPI
from .sales import SalesSnapshotsAPI
from .bills import (
    BillsAPI,
    ConnectorsAPI,
    CashierModuleExtensionsAPI,
    ChecksAPI,
    ConnectorTasksAPI,
    CorrectionsAPI,
    SecurityAPI,
    PointsOfSaleAPI,
    PointOfSaleBillHashAPI,
    ProjectsAPI,
    ResponsibilityZonesAPI,
    StatusAPI,
    Status2TenantAPI,
    TenantsAPI,
    TenantStatusAPI,
    TenantCommentsAPI,
)


DEFAULT_CORE_API_ENDPOINT = "https://api.focustech.xyz"
DEFAULT_SALES_API_ENDPOINT = "https://fsf-api.focustech.xyz/api"
DEFAULT_BILLS_API_ENDPOINT = "https://fsf-api.focustech.xyz"


class MallsenseSDK:
    """Unified client for the Mallsense platform.

    Configuration precedence for `token`, `app_key`, and base URLs:

    1) Explicit arguments in constructor
    2) Config file at `~/.mallsense-sdk-conf.json`
    3) Environment variables

    Environment variables:
    - `MALLSENSE_X_TOKEN`
    - `MALLSENSE_X_APP_KEY`
    - `MALLSENSE_CORE_ENDPOINT` (default: https://api.focustech.xyz)
    - `MALLSENSE_SALES_ENDPOINT` (default: https://fsf-api.focustech.xyz/api)
    - `MALLSENSE_BILLS_ENDPOINT` (default: https://fsf-api.focustech.xyz)
    """

    def __init__(
        self,
        *,
        token: Optional[str] = None,
        app_key: Optional[str] = None,
        core_base_url: Optional[str] = None,
        sales_base_url: Optional[str] = None,
        bills_base_url: Optional[str] = None,
        config_path: Optional[str] = None,
        # HTTP options (applied to all service clients)
        verify: Optional[bool | str] = None,
        cert: Optional[str | tuple[str, str]] = None,
        proxies: Optional[dict[str, str]] = None,
        pool_connections: int = 10,
        pool_maxsize: int = 50,
        # Per-service HTTP overrides (merged over the global options)
        core_http_options: Optional[dict] = None,
        sales_http_options: Optional[dict] = None,
        bills_http_options: Optional[dict] = None,
    ):
        # Resolve configuration
        conf_file_path = os.path.expanduser(
            config_path or "~/.mallsense-sdk-conf.json"
        )
        CONF_TOKEN = "MALLSENSE_X_TOKEN"
        CONF_APP_KEY = "MALLSENSE_X_APP_KEY"
        CONF_CORE_ENDPOINT = "MALLSENSE_CORE_ENDPOINT"
        CONF_SALES_ENDPOINT = "MALLSENSE_SALES_ENDPOINT"
        CONF_BILLS_ENDPOINT = "MALLSENSE_BILLS_ENDPOINT"

        file_conf = {}
        if os.path.exists(conf_file_path):
            try:
                file_conf = json.loads(open(conf_file_path).read())
            except Exception:
                file_conf = {}

        token = token or file_conf.get(CONF_TOKEN) or os.environ.get(CONF_TOKEN)
        app_key = app_key or file_conf.get(CONF_APP_KEY) or os.environ.get(CONF_APP_KEY)
        if not token or not app_key:
            raise ValueError("'token' and 'app_key' must be provided")

        core_base_url = (
            core_base_url
            or file_conf.get(CONF_CORE_ENDPOINT)
            or os.environ.get(CONF_CORE_ENDPOINT)
            or DEFAULT_CORE_API_ENDPOINT
        )
        sales_base_url = (
            sales_base_url
            or file_conf.get(CONF_SALES_ENDPOINT)
            or os.environ.get(CONF_SALES_ENDPOINT)
            or DEFAULT_SALES_API_ENDPOINT
        )
        bills_base_url = (
            bills_base_url
            or file_conf.get(CONF_BILLS_ENDPOINT)
            or os.environ.get(CONF_BILLS_ENDPOINT)
            or DEFAULT_BILLS_API_ENDPOINT
        )

        # Compose app-key used by backend for client identification
        x_app_key = f"mallsense-sdk/{app_key}"

        # HTTP clients per service domain
        http_kwargs = dict(
            verify=verify,
            cert=cert,
            proxies=proxies,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
        )
        def _merge(base: dict, extra: Optional[dict]) -> dict:
            m = dict(base)
            if extra:
                m.update(extra)
            return m

        core_http = HTTPApi(
            token=token,
            app_key=x_app_key,
            base_url=core_base_url,
            **_merge(http_kwargs, core_http_options),
        )
        sales_http = HTTPApi(
            token=token,
            app_key=x_app_key,
            base_url=sales_base_url,
            **_merge(http_kwargs, sales_http_options),
        )
        bills_http = HTTPApi(
            token=token,
            app_key=x_app_key,
            base_url=bills_base_url,
            **_merge(http_kwargs, bills_http_options),
        )

        # Sub-clients
        self.metrics = MetricsAPI(core_http)
        self.structure = StructureAPI(core_http)

        self.sales = SalesSnapshotsAPI(sales_http)

        self.bills = BillsAPI(bills_http)
        self.connectors = ConnectorsAPI(bills_http)
        self.cashier_extensions = CashierModuleExtensionsAPI(bills_http)
        self.status = StatusAPI(bills_http)
        self.checks = ChecksAPI(bills_http)
        self.connector_tasks = ConnectorTasksAPI(bills_http)
        self.corrections = CorrectionsAPI(bills_http)
        self.security = SecurityAPI(bills_http)
        self.points_of_sale = PointsOfSaleAPI(bills_http)
        self.pos_bill_hash = PointOfSaleBillHashAPI(bills_http)
        self.projects = ProjectsAPI(bills_http)
        self.responsibility_zones = ResponsibilityZonesAPI(bills_http)
        self.status2tenant = Status2TenantAPI(bills_http)
        self.jobs = JobsAPI(bills_http)
        self.tenants = TenantsAPI(bills_http)
        self.tenant_status = TenantStatusAPI(bills_http)
        self.tenant_comments = TenantCommentsAPI(bills_http)
        # Snapshot endpoints exposed via Bills base URL
        from .bills.snapshots import BillsSalesSnapshotsAPI
        self.bills_snapshots = BillsSalesSnapshotsAPI(bills_http)
