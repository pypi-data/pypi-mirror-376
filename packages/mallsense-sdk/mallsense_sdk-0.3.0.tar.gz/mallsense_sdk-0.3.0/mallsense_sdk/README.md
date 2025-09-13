# Mallsense SDK — Package Guide

## Introduction

This package provides the Python implementation of the Mallsense SDK. It bundles clients for Core (Dashboard), Sales, and Bills services, a robust HTTP layer, and strict request models.

## Purpose

- Explain the package layout and entry points
- Show quick initialization and representative usage
- Document configuration options and environment variables

- Unified SDK for Core Dashboard, Sales Snapshots, and Bills/Connectors services.
- Strongly typed method interfaces, robust retries, and clear documentation.

Requirements

- Python 3.8+
- Packages: `requests`, `pandas`, `python-dateutil`

Documentation

- Full documentation (GitLab):
  - Index: https://gitlab.focustech.xyz/service.head/mallsense-sdk/-/blob/main/docs/index.md
  - Core (Dashboard): https://gitlab.focustech.xyz/service.head/mallsense-sdk/-/blob/main/docs/core.md
  - Sales Snapshots: https://gitlab.focustech.xyz/service.head/mallsense-sdk/-/blob/main/docs/sales.md
  - Bills: https://gitlab.focustech.xyz/service.head/mallsense-sdk/-/blob/main/docs/bills.md
  - Connectors: https://gitlab.focustech.xyz/service.head/mallsense-sdk/-/blob/main/docs/connectors.md
  - Status: https://gitlab.focustech.xyz/service.head/mallsense-sdk/-/blob/main/docs/status.md
  - Checks & Jobs: https://gitlab.focustech.xyz/service.head/mallsense-sdk/-/blob/main/docs/checks_jobs.md
  - Tenants & Comments: https://gitlab.focustech.xyz/service.head/mallsense-sdk/-/blob/main/docs/tenants.md
  - Points of Sale: https://gitlab.focustech.xyz/service.head/mallsense-sdk/-/blob/main/docs/pos.md
  - Models Index: https://gitlab.focustech.xyz/service.head/mallsense-sdk/-/blob/main/docs/models.md

Package Layout

- `mallsense_sdk/`
  - `api.py` – main `MallsenseSDK` entry point
  - `http.py` – shared HTTP client (retries, headers, CSV query)
  - `models.py` – strict request models (auto‑generated)
  - `core/` – Core Dashboard clients (metrics, structure)
  - `sales/` – Sales snapshots client
  - `bills/` – Bills service clients (bills, connectors, checks, jobs, POS, tenants, status, etc.)


Install

- From PyPI (recommended):

```bash
pip install mallsense-sdk
```

- From source (editable):

```bash
pip install -e .
```

Initialize

```
from mallsense_sdk import MallsenseSDK

sdk = MallsenseSDK(
    token="<x-token>",
    app_key="<x-app-key>",
    core_base_url="https://api.focustech.xyz",           # Core Dashboard API
    sales_base_url="https://fsf-api.focustech.xyz/api",  # Sales Snapshots API
    # bills_base_url defaults to https://fsf-api.focustech.xyz
)

# Metrics (Core Dashboard API)
df = sdk.metrics.get_metric(
    metric="fpc_sum_pass_count_in_wh",
    obj_ids=[3208],
    time_range=["2024-01-01", "2024-01-31"],
    time_freq="D",
)

```

Configuration

- Precedence: constructor args > `~/.mallsense-sdk-conf.json` > environment
- Config file path can be customized via `config_path`.
- Example config file `~/.mallsense-sdk-conf.json`:

```
{
  "MALLSENSE_X_TOKEN": "...",
  "MALLSENSE_X_APP_KEY": "...",
  "MALLSENSE_CORE_ENDPOINT": "https://api.focustech.xyz",
  "MALLSENSE_SALES_ENDPOINT": "https://fsf-api.focustech.xyz/api",
  "MALLSENSE_BILLS_ENDPOINT": "https://fsf-api.focustech.xyz"
}
```

- Environment variables (if present):
  - `MALLSENSE_X_TOKEN`
  - `MALLSENSE_X_APP_KEY`
  - `MALLSENSE_CORE_ENDPOINT` (default: `https://api.focustech.xyz`)
  - `MALLSENSE_SALES_ENDPOINT` (default: `https://fsf-api.focustech.xyz/api`)
  - `MALLSENSE_BILLS_ENDPOINT` (default: `https://fsf-api.focustech.xyz`)

Core Dashboard API

- Metrics: `sdk.metrics` (returns pandas DataFrame)
  - `get_metric(metric, obj_ids, time_range, time_freq='D', alias=None, metric_level=None, object_aggregation=False)`
  - `get_metrics_bulk(metrics, obj_ids, time_range, time_freq='D', metric_level=None, object_aggregation=False)`
  - Notes:
    - Supports all metric names, including extended metrics.
    - Automatically batches high‑frequency windows (e.g., 15MIN/H > 31 days).

- Structure: `sdk.structure`
  - `get_pl_info(pl_id=None)` – all PLs or by id
  - `get_metrics_list()` – available metrics
  - `get_structure_table(pl_id, structure_table)` – tables: core/* and fpc/* (full list mirrors legacy SDK).

Sales Snapshots API

- `sdk.sales` (via Sales base URL)
  - `get_snapshot(project_location_id, date_from, date_to, actuality_time=None, tenant_ids=None, accept='application/json')`
  - `get_snapshot_diff(project_location_id, date_from, date_to, actuality_time_from, actuality_time_to, tenant_ids=None, accept='application/json')`
  - `get_snapshot_history(project_location_id, date_from, date_to, tenant_ids=None, updated_from=None, updated_to=None)`

- `sdk.bills_snapshots` (same endpoints via Bills base URL)

Bills + Connectors API (full coverage)

- Bills: `sdk.bills`
  - `list_bills_full(date_from, date_to, bill_type=None, connector_type=None, limit=None, offset=None, point_of_sale_ids=None, tenant_ids=None)`
  - `list_bills_short(date_from, date_to, bill_type=None, connector_type=None, limit=None, offset=None, point_of_sale_ids=None, tenant_ids=None)`
  - `list_bills_simple(date_from, date_to, bill_type=None, connector_type=None, limit=None, offset=None, point_of_sale_ids=None, tenant_ids=None)`

- Connectors (discovery and CRUD): `sdk.connectors`
  - Discovery: `list_types()`
  - Aggregated listing: `list_connectors(connector_types=None, date_from=None, date_to=None, project_location_id=None, project_location_ids=None, tenant_id=None, limit=None, offset=None)`
  - Manage a specific connector type (examples use "nifi"):
    - `list('nifi', limit=None, offset=None)`
    - `create('nifi', payload)`
    - `retrieve('nifi', connector_id)`
    - `update('nifi', connector_id, payload)`
    - `partial_update('nifi', connector_id, payload)`
    - `delete('nifi', connector_id)`

- Cashier Module Extensions: `sdk.cashier_extensions`
  - `list(limit=None, offset=None)`
  - `create(payload)`
  - `retrieve(extension_id)`
  - `update(extension_id, payload)`
  - `partial_update(extension_id, payload)`
  - `delete(extension_id)`

- Connector Tasks: `sdk.connector_tasks`
  - `list(**filters)` – filters include attempt[], connector_ids[], connector_types[], created_from/to, date_from/to, project_location_ids, status, tenant_ids, limit/offset
  - `retrieve(task_id)`

- Jobs (create/cancel tasks): `sdk.jobs`
  - `create(payload)` – POST `/api/task-creator/`
  - `cancel(payload)` – POST `/api/task-canceler/`

- Checks: `sdk.checks`
  - `get_check_result()` – GET `/api/check-result/`
  - `get_check_result_detail()` – GET `/api/check-result-detail/`
  - `update_check_result_status(id, payload)` – PUT `/api/check-result-status-update/{id}/`
  - `partial_update_check_result_status(id, payload)` – PATCH `/api/check-result-status-update/{id}/`

- Corrections: `sdk.corrections`
  - `first_bill_date(project_location_ids, tenant_ids=None)` – GET `/api/correction/first-bill-date/`

- Security/Utility: `sdk.security`
  - `create_l4l_filtration_jwt()` – POST `/api/l4l-filtration-jwt/`

- Points of Sale: `sdk.points_of_sale`
  - `list(connector_ids=None, date_from=None, date_to=None, pos_date_from=None, pos_date_to=None, project_location_id=None, project_location_ids=None, tenant_id=None, tenant_ids=None, without_data=None, limit=None, offset=None)`
  - `partial_update(id, payload)` – PATCH `/api/points-of-sale/{id}/`
  - `delete(id)` – DELETE `/api/points-of-sale/{id}/`

- Point-of-Sale Bill Hash: `sdk.pos_bill_hash`
  - `list(date_from=None, date_to=None, point_of_sale_ids=None, tenant_ids=None, updated_after=None, updated_before=None, limit=None, offset=None)`

- Project Locations (Bills): `sdk.projects`
  - `list(limit=None, offset=None)` – GET `/api/project-locations/`

- Responsibility Zones: `sdk.responsibility_zones`
  - `list(limit=None, offset=None)` – GET `/api/responsibility-zone/`

- Status (Points of Sale): `sdk.status`
  - Auto: `list_point_of_sale_auto(date_from, date_to, project_location_ids, is_latest_status=None, status=None, point_of_sale_ids=None, tenant_ids=None, updated_from=None, updated_to=None, limit=None, offset=None)`
  - Manual: `list_point_of_sale_manual(date_from=None, date_to=None, project_location_ids=None, status=None, point_of_sale_ids=None, tenant_ids=None, updated_from=None, updated_to=None, user_ids=None, limit=None, offset=None)`
  - Manual: `create_point_of_sale_manual(payload)`

- Status to Tenant assignments: `sdk.status2tenant`
  - `list(assigned_from=None, assigned_to=None, created_from=None, created_to=None, project_location_ids=None, tenant_ids=None, updated_from=None, updated_to=None, user_ids=None, limit=None, offset=None)`
  - `create(payload)`
  - `update(id, payload)`
  - `partial_update(id, payload)`
  - `delete(id)`

- Tenants and Statuses: `sdk.tenants`, `sdk.tenant_status`
  - Tenants: `list(project_location_id=None, project_location_ids=None, limit=None, offset=None)`
  - Tenant Status: `list(limit=None, offset=None)`

- Tenant Comments: `sdk.tenant_comments`
  - `list(assigned_from=None, assigned_to=None, comment_type=None, project_location_ids=None, responsibility_zone_ids=None, tenant_ids=None, user_ids=None, limit=None, offset=None)`
  - `create(payload)`
  - `update(id, payload)`
  - `partial_update(id, payload)`

Metrics Usage Examples

```
# Single metric
df = sdk.metrics.get_metric(
    metric="fpc_sum_pass_count_in_wh",
    obj_ids=[3208],
    time_range=["2024-01-01", "2024-01-31"],
    time_freq="D",
)

# Bulk metrics
df_many = sdk.metrics.get_metrics_bulk(
    metrics=["fpc_sum_pass_count_in_wh", "fpc_avg_dwell_time"],
    obj_ids=[3208],
    time_range=["2024-01-01", "2024-01-31"],
)

# Structure (Core Dashboard API)
pl = sdk.structure.get_pl_info(201)
zone_df = sdk.structure.get_structure_table(201, "core/relations_place2zone")

# Sales snapshots (Sales API)
snap = sdk.sales.get_snapshot(
    project_location_id=201,
    date_from="2024-01-01",
    date_to="2024-01-31",
)

# Bills (Bills API)
bills_full = sdk.bills.list_bills_full(
    date_from="2024-01-01",
    date_to="2024-01-31",
    tenant_ids=[101, 102],
)

# Connectors (Bills API)
types = sdk.connectors.list_types()
all_nifi = sdk.connectors.list("nifi", limit=100)

created = sdk.connectors.create("nifi", payload={"name": "My NiFi", "active": True})
fetched = sdk.connectors.retrieve("nifi", created["id"])
updated = sdk.connectors.update("nifi", created["id"], payload={"active": False})
sdk.connectors.delete("nifi", created["id"])  # No return body

# Cashier Module Extensions (Bills API)
exts = sdk.cashier_extensions.list(limit=50)
new_ext = sdk.cashier_extensions.create({"name": "Ext A"})
sdk.cashier_extensions.delete(new_ext["id"])

# Status (Bills API)
status = sdk.status.list_point_of_sale_auto(
    date_from="2024-01-01",
    date_to="2024-01-07",
    project_location_ids=[201],
    is_latest_status=True,
)

# Checks and Tasks (Bills API)
check = sdk.checks.get_check_result()
tasks = sdk.connector_tasks.list(attempt=[1, 2], status=["pending", "success"])  # example filters
```

Strict Models and Payload Validation

- Methods that send JSON bodies accept typed Pydantic models and will validate payloads strictly against the API contract. Extra fields are rejected.
- You may also pass plain dicts; the SDK validates and raises a clear error if invalid.

Examples

- Cashier Module Extensions
```
from mallsense_sdk.models import Extension, PatchedExtension

ext = Extension(connector=123, name="ext-a", version="1.0.0", config={"k": "v"})
created = sdk.cashier_extensions.create(ext)
sdk.cashier_extensions.partial_update(created["id"], PatchedExtension(version="1.0.1"))
```

- Checks: Update status
```
from mallsense_sdk.models import CheckResultStatusUpdate
sdk.checks.update_check_result_status(42, CheckResultStatusUpdate(status="solved"))
```

- Jobs: Create/cancel tasks
```
from mallsense_sdk.models import TaskCreatorInput
task = TaskCreatorInput(date_from="2024-01-01", date_to="2024-01-31", project_location_ids=[201])
sdk.jobs.create(task)
sdk.jobs.cancel(task)
```

- Status (manual): Create
```
from mallsense_sdk.models import StatusPointOfSaleManualCreate
sdk.status.create_point_of_sale_manual(
    StatusPointOfSaleManualCreate(point_of_sale=555, date="2024-01-20", status="no_sale")
)
```

- Status ↔ Tenant assignments
```
from mallsense_sdk.models import Status2Tenant, PatchedStatus2Tenant
created = sdk.status2tenant.create(Status2Tenant(tenant_id=1001, tenant_status_id=5, user_id=7))
sdk.status2tenant.partial_update(created["id"], PatchedStatus2Tenant(assigned_at="2024-01-21T10:00:00Z"))
```

- Tenant comments
```
from mallsense_sdk.models import TenantComment, PatchedTenantComment
comment = TenantComment(
  tenant={"id": 1001, "project_location": 201, "name": "Acme", "marker": "acme", "is_active": True},
  status2tenant={"tenant_id": 1001, "tenant_status_id": 5, "user_id": 7},
  responsibility_zone={"id": 1, "name": "Default", "project_location": 201},
  user_id=7,
  comment_type="comment",
  message="Investigate POS connectivity."
)
sdk.tenant_comments.create(comment)
```

- Points of Sale: partial update
```
from mallsense_sdk.models import PatchedPointOfSaleUpdate
sdk.points_of_sale.partial_update(1234, PatchedPointOfSaleUpdate(date_from="2024-01-01"))
```

- Connectors: strongly-typed payloads per connector type
```
from mallsense_sdk.models import NifiSerializer, PatchednifiSerializer
# Create
nifi = NifiSerializer(tenant=999, port=8443, config={"base_url": "https://nifi-host", "flow_id": "..."})
sdk.connectors.create("nifi", nifi)
# Patch
sdk.connectors.partial_update("nifi", 321, PatchednifiSerializer(is_active=False))
```

Error Handling

- Non‑2xx responses raise `HTTPApi.ServerError` with URL, status code, response excerpt, headers, params, and body details.
- Timeouts raise `HTTPApi.TimeoutError` (configurable retries with backoff).

Parameter Encoding

- List parameters are encoded as comma‑separated values (CSV) to match API expectations.
- Booleans are encoded as `true`/`false` strings.

Authentication

- `x-token` and `x-app-key` are automatically injected into every request header.
- `x-app-key` identifies your application as `mallsense-sdk/<app-key>`.

API Index

- Bills
  - `sdk.bills.list_bills_full(...)` – GET `/api/bills-full/` (no JSON body)
  - `sdk.bills.list_bills_short(...)` – GET `/api/bills-short/` (no JSON body)
  - `sdk.bills.list_bills_simple(...)` – GET `/api/bills-simple/` (no JSON body)

- Connectors
  - Discovery: `sdk.connectors.list_types()` – GET `/api/manage-connectors/connector-types/` (no JSON body)
  - Aggregated listing: `sdk.connectors.list_connectors(...)` – GET `/api/connectors/` (no JSON body)
  - Manage a specific connector type
    - Create: `sdk.connectors.create(connector_type, payload)` – POST `/api/manage-connectors/{type}/`
      - Input model: `{Type}Serializer` (e.g., `NifiSerializer`)
      - Required fields vary by type (see models); Example (nifi):
        ```json
        {
          "tenant": 999,
          "port": 8443,
          "config": {"base_url": "https://nifi-host", "flow_id": "..."}
        }
        ```
    - Update: `sdk.connectors.update(type, id, payload)` – PUT `/api/manage-connectors/{type}/{id}/`
      - Input model: `{Type}Serializer` (same required fields as create)
    - Patch: `sdk.connectors.partial_update(type, id, payload)` – PATCH `/api/manage-connectors/{type}/{id}/`
      - Input model: `Patched{Type}Serializer` (all fields optional)

- Cashier Module (Extensions)
  - List: `sdk.cashier_extensions.list(...)` – GET `/api/cashier-module/extensions/` (no JSON body)
  - Create: `sdk.cashier_extensions.create(payload)` – POST `/api/cashier-module/extensions/`
    - Input model: `Extension`
    - Required: `connector`, `name`, `version`
    - Example:
      ```json
      {"connector": 123, "name": "ext-a", "version": "1.0.0", "config": {"k": "v"}}
      ```
  - Update: `sdk.cashier_extensions.update(id, payload)` – PUT `/api/cashier-module/extensions/{id}/`
    - Input model: `Extension` (same required)
  - Patch: `sdk.cashier_extensions.partial_update(id, payload)` – PATCH `/api/cashier-module/extensions/{id}/`
    - Input model: `PatchedExtension` (all fields optional)

- Checks
  - List: `sdk.checks.get_check_result()` – GET `/api/check-result/`
  - Detail: `sdk.checks.get_check_result_detail()` – GET `/api/check-result-detail/`
  - Update status: `sdk.checks.update_check_result_status(id, payload)` – PUT `/api/check-result-status-update/{id}/`
    - Input model: `CheckResultStatusUpdate`
    - Required: `status` (one of `active|solved|closed`)
    - Example: `{ "status": "solved", "project_location_ids": [201, 202] }`
  - Patch status: `sdk.checks.partial_update_check_result_status(id, payload)` – PATCH `/api/check-result-status-update/{id}/`
    - Input model: `PatchedCheckResultStatusUpdate`

- Connector Tasks
  - List: `sdk.connector_tasks.list(**filters)` – GET `/api/connector-task/` (no JSON body)
  - Retrieve: `sdk.connector_tasks.retrieve(id)` – GET `/api/connector-task/{id}/` (no JSON body)

- Jobs
  - Create: `sdk.jobs.create(payload)` – POST `/api/task-creator/`
    - Input model: `TaskCreatorInput`
    - Required: `date_from`, `date_to`, `project_location_ids`
    - Example:
      ```json
      {"date_from":"2024-01-01","date_to":"2024-01-31","project_location_ids":[201],"tenant_ids":[101,102]}
      ```
  - Cancel: `sdk.jobs.cancel(payload)` – POST `/api/task-canceler/`
    - Input model: `TaskCreatorInput` (same shape)

- Corrections
  - First bill date: `sdk.corrections.first_bill_date(project_location_ids, tenant_ids=None)` – GET `/api/correction/first-bill-date/` (no JSON body)

- Security
  - Create filtration token: `sdk.security.create_l4l_filtration_jwt()` – POST `/api/l4l-filtration-jwt/` (no body)

- Points of Sale
  - List: `sdk.points_of_sale.list(...)` – GET `/api/points-of-sale/` (no JSON body)
  - Patch: `sdk.points_of_sale.partial_update(id, payload)` – PATCH `/api/points-of-sale/{id}/`
    - Input model: `PatchedPointOfSaleUpdate`
    - Example: `{ "date_from": "2024-01-01" }`
  - Delete: `sdk.points_of_sale.delete(id)` – DELETE `/api/points-of-sale/{id}/`

- Point-of-Sale Bill Hash
  - List: `sdk.pos_bill_hash.list(...)` – GET `/api/point-of-sale-bill-hash/` (no JSON body)

- Projects & Responsibility Zones
  - Projects: `sdk.projects.list(...)` – GET `/api/project-locations/` (no JSON body)
  - Responsibility Zones: `sdk.responsibility_zones.list(...)` – GET `/api/responsibility-zone/` (no JSON body)

- Sales Snapshots (via Bills base)
  - `sdk.bills_snapshots.get_snapshot(...)` – GET `/api/snapshot/` (no JSON body)
  - `sdk.bills_snapshots.get_snapshot_diff(...)` – GET `/api/snapshot-diff/` (no JSON body)
  - `sdk.bills_snapshots.get_snapshot_history(...)` – GET `/api/snapshot-history/` (no JSON body)

- Status (Points of Sale)
  - Auto list: `sdk.status.list_point_of_sale_auto(...)` – GET `/api/status-point-of-sale-auto/` (no JSON body)
  - Manual list: `sdk.status.list_point_of_sale_manual(...)` – GET `/api/status-point-of-sale-manual/` (no JSON body)
  - Manual create: `sdk.status.create_point_of_sale_manual(payload)` – POST `/api/status-point-of-sale-manual/`
    - Input model: `StatusPointOfSaleManualCreate`
    - Required: `point_of_sale`
    - Example: `{ "point_of_sale": 555, "date": "2024-01-20", "status": "no_sale" }`

- Status ↔ Tenant
  - List: `sdk.status2tenant.list(...)` – GET `/api/status2tenant/` (no JSON body)
  - Create: `sdk.status2tenant.create(payload)` – POST `/api/status2tenant/`
    - Input model: `Status2Tenant`
    - Required: `tenant_id`, `tenant_status_id`, `user_id`
  - Update: `sdk.status2tenant.update(id, payload)` – PUT `/api/status2tenant/{id}/`
    - Input model: `Status2Tenant`
  - Patch: `sdk.status2tenant.partial_update(id, payload)` – PATCH `/api/status2tenant/{id}/`
    - Input model: `PatchedStatus2Tenant`
  - Delete: `sdk.status2tenant.delete(id)` – DELETE (no JSON body)

- Tenants & Tenant Statuses
  - Tenants: `sdk.tenants.list(...)` – GET `/api/tenants/` (no JSON body)
  - Tenant Status: `sdk.tenant_status.list(...)` – GET `/api/tenant-status/` (no JSON body)

- Tenant Comments
  - List: `sdk.tenant_comments.list(...)` – GET `/api/tenant-comment/` (no JSON body)
  - Create: `sdk.tenant_comments.create(payload)` – POST `/api/tenant-comment/`
    - Input model: `TenantComment`
    - Required: `tenant`, `status2tenant`, `responsibility_zone`, `user_id`, `comment_type`, `message`
  - Update: `sdk.tenant_comments.update(id, payload)` – PUT `/api/tenant-comment/{id}/`
    - Input model: `TenantComment`
  - Patch: `sdk.tenant_comments.partial_update(id, payload)` – PATCH `/api/tenant-comment/{id}/`
    - Input model: `PatchedTenantComment`

Models Reference

- See `mallsense_sdk/models.py` for all request models and enums. Models are strict: extra fields are rejected; nullable fields and optionals are handled per spec. Use `.to_payload()` on a model to get the final JSON the SDK sends.
