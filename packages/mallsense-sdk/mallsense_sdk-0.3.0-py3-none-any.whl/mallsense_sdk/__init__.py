"""
Mallsense SDK
-------------

High-level Python SDK for interacting with Mallsense services:

- Core Dashboard API (metrics, structure)
- Sales Snapshots API
- Bills and Connector Management API

Usage example:

    from mallsense_sdk import MallsenseSDK

    sdk = MallsenseSDK(
        token="<x-token>",
        app_key="<x-app-key>",
        core_base_url="https://api.focustech.xyz",
        sales_base_url="https://fsf-api.focustech.xyz/api",
        # bills_base_url defaults to https://fsf-api.focustech.xyz
    )

    # Metrics
    df = sdk.metrics.get_metric(
        metric="fpc_sum_pass_count_in_wh",
        obj_ids=[3208],
        time_range=["2024-01-01", "2024-01-31"],
        time_freq="D",
    )

    # Bills (full)
    bills = sdk.bills.list_bills_full(
        date_from="2024-01-01",
        date_to="2024-01-31",
        tenant_ids=[101, 102],
    )

"""

from .api import MallsenseSDK
from .utils import generate_idempotency_key, with_idempotency

__all__ = ["MallsenseSDK", "generate_idempotency_key", "with_idempotency"]
