# Mallsense SDK (Python)

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
