# Mallsense SDK (Python)

![PyPI](https://img.shields.io/pypi/v/mallsense-sdk.svg?logo=pypi&label=PyPI)
![Python Versions](https://img.shields.io/pypi/pyversions/mallsense-sdk.svg)
![GitLab pipeline status](https://img.shields.io/gitlab/pipeline-status/gitlab.focustech.xyz/service.head/mallsense-sdk?branch=main)

## Introduction

The Mallsense SDK unifies access to Core (Dashboard), Sales, and Bills services with consistent authentication, robust HTTP behavior, and strict payload validation.

## Purpose

- Provide a friendly, typed interface over all major Mallsense APIs
- Offer beginner‑friendly docs, recipes, and error‑handling guidance
- Keep endpoints and models in sync with coverage maps and CI

Unified Python SDK for Mallsense services:
- Core Dashboard (metrics, structure)
- Sales Snapshots
- Bills and Connectors (full coverage)

Quick links

- Documentation Index: [docs/index.md](docs/index.md)
- Getting Started: [docs/getting_started.md](docs/getting_started.md)
- Coverage Map: [docs/coverage.md](docs/coverage.md)
- Package Guide: [mallsense_sdk/README.md](mallsense_sdk/README.md)
- Examples: [examples/README.md](examples/README.md)

Installation

From PyPI:

```bash
pip install mallsense-sdk
```

From source (this repository):

```bash
pip install -e .
```

Quick start

```python
from mallsense_sdk import MallsenseSDK

sdk = MallsenseSDK(
  token="<x-token>",
  app_key="<x-app-key>",
  # core_base_url="https://api.focustech.xyz",              # default
  # sales_base_url="https://fsf-api.focustech.xyz/api",     # default
  # bills_base_url="https://fsf-api.focustech.xyz",         # default
)

# Fetch a metric (Core)
df = sdk.metrics.get_metric(
  metric="fpc_sum_pass_count_in_wh",
  obj_ids=[3208],
  time_range=["2024-01-01", "2024-01-31"],
  time_freq="D",
)

# List bills (Bills)
bills = sdk.bills.list_bills_full(
  date_from="2024-01-01",
  date_to="2024-01-31",
)
```

HTTP options (proxies/TLS/pooling)

You can set HTTP options globally (applied to all services) and/or override per service.

```python
from mallsense_sdk import MallsenseSDK

sdk = MallsenseSDK(
  token="...",
  app_key="...",
  # Global HTTP options
  verify="/etc/ssl/certs/ca-bundle.crt",
  proxies={"https": "http://proxy.internal:8080"},
  pool_connections=20,
  pool_maxsize=100,
  # Per-service overrides
  core_http_options={"verify": True},
  sales_http_options={"proxies": {"https": "http://sales-proxy:8080"}},
  bills_http_options={"verify": "/opt/certs/bills-ca.pem"},
)
```

Streaming and pagination helpers

- Stream large snapshots as ZIP/GZ bytes:

```python
with open("snapshot.zip", "wb") as fh:
  for chunk in sdk.sales.get_snapshot_stream(project_location_id=201, date_from="2024-01-01", date_to="2024-01-31", accept="application/zip"):
    fh.write(chunk)
```

- Iterate lists without manual offset management:

```python
for bill in sdk.bills.iter_bills_full(date_from="2024-01-01", date_to="2024-01-31", limit=1000):
  pass

for pos in sdk.points_of_sale.iter(project_location_ids=[201], limit=500):
  pass
```

Safe retries for writes (Idempotency-Key)

Use an Idempotency-Key to safely retry POST/PUT/PATCH operations:

```python
from mallsense_sdk import with_idempotency
from mallsense_sdk.models import NifiSerializer

payload = NifiSerializer(tenant=999, port=8443, config={"base_url": "https://nifi-host"})
sdk.connectors.create("nifi", payload, headers=with_idempotency())
```

Environment variables

You can omit constructor arguments by setting these env vars or using a config file:

- `MALLSENSE_X_TOKEN`
- `MALLSENSE_X_APP_KEY`
- `MALLSENSE_CORE_ENDPOINT` (default: https://api.focustech.xyz)
- `MALLSENSE_SALES_ENDPOINT` (default: https://fsf-api.focustech.xyz/api)
- `MALLSENSE_BILLS_ENDPOINT` (default: https://fsf-api.focustech.xyz)

More

- See `mallsense_sdk/README.md` for extended examples, tips, and recipes.
- See `docs/*.md` for detailed service docs and strict payload models.

Running tests

Recommended (virtual environment):

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
pip install pytest
pytest -q
```

Publishing

Build and upload a release to PyPI (or your internal index):

```bash
# 1) Build sdist and wheel
python -m pip install --upgrade build twine
python -m build

# 2) Verify artifacts
twine check dist/*

# 3) Upload (with an API token)
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # or your index token
twine upload dist/*

# Optional: test upload to TestPyPI
# twine upload --repository testpypi dist/*
```

Notes

- Distributions exclude large/spec reference files and developer-only content (docs, tests, scripts).
- Runtime dependencies are pinned with upper/lower bounds for reliable installs:
  - requests>=2.31,<3; pandas>=2,<3; pydantic>=2.3,<3; python-dateutil>=2.8.2,<3; pytz>=2023.3,<2026; python-dotenv>=1.0,<2

Makefile and CI

- Use `make release` for a one-shot build/check/verify/publish flow. See `Makefile` targets with `make help`.
- See `RELEASE.md` for a full release checklist and tagging steps.
- GitLab CI (`.gitlab-ci.yml`) publishes on tags matching `vX.Y.Z` when `TWINE_USERNAME` and `TWINE_PASSWORD` are set in CI variables.

If you see “ensurepip is not available” when creating the venv on Debian/Ubuntu, install the venv package first:

```bash
sudo apt install python3-venv
```

Alternatively (PEP 668 / system Python):

Some distros protect the system Python. If `pip install` warns about an externally managed environment, you can either use a venv (recommended) or explicitly allow system installs:

```bash
python3 -m pip install --break-system-packages -e . pytest
pytest -q
```
