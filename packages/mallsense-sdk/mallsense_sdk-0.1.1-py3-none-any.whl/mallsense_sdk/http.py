from __future__ import annotations

"""HTTP client utilities for the Mallsense SDK.

Provides a robust request wrapper with retries, backoff, structured exceptions,
parameter encoding, and optional correlation IDs.
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, Mapping, MutableMapping, Optional, Union

import requests

from .exceptions import ClientError, ServerError, TimeoutError, NetworkError, JSONDecodeError


Headers = Mapping[str, str]
ParamsValue = Union[str, int, float, bool, None]
Params = MutableMapping[str, ParamsValue]


logger = logging.getLogger("mallsense_sdk")


class HTTPApi:
    """Small HTTP client wrapper with retries and helpful errors.

    - Adds x-token/x-app-key headers
    - Encodes list-like query params as comma-separated values (CSV)
    - Retries timeouts and non-2xx with exponential backoff
    - Raises structured exceptions with request/response context
    """

    def __init__(self, token: str, app_key: str, base_url: str):
        self.token = token
        self.app_key = app_key
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _redact_headers(h: Mapping[str, Any]) -> Dict[str, Any]:
        redacted = dict(h)
        for k in ("x-token", "x-app-key", "authorization"):
            if k in redacted:
                redacted[k] = "[redacted]"
        return redacted

    def _headers(self, extra: Optional[Headers] = None) -> Dict[str, str]:
        headers = {
            "x-token": self.token,
            "x-app-key": self.app_key,
        }
        if extra:
            headers.update(extra)
        # ensure a correlation id is present
        headers.setdefault("x-correlation-id", uuid.uuid4().hex)
        return headers

    @staticmethod
    def _encode_params(params: Optional[Mapping[str, Any]]) -> Params:
        encoded: Params = {}
        if not params:
            return encoded
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, (list, tuple, set)):
                encoded[k] = ",".join(str(x) for x in v)
            elif isinstance(v, bool):
                encoded[k] = "true" if v else "false"
            else:
                encoded[k] = str(v)
        return encoded

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Headers] = None,
        json_body: Optional[Mapping[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
        attempts: int = 3,
        sleep_non_200: float = 1.0,
        sleep_timeout: float = 1.5,
        timeout: float = 60.0,
    ) -> Any:
        """Perform an HTTP request with retries and helpful errors.

        Parameters:
        - method: HTTP verb (GET|POST|PUT|PATCH|DELETE)
        - path: Path appended to `base_url`
        - headers: Extra headers; `x-token`/`x-app-key` are set automatically
        - json_body: JSON body for POST/PUT/PATCH
        - params: Query params (lists encoded as CSV)
        - attempts: Total retry attempts (>= 1)
        - sleep_non_200: Initial backoff for non‑2xx (seconds)
        - sleep_timeout: Initial backoff for timeouts (seconds)
        - timeout: Per‑request timeout (seconds)
        """
        url = f"{self.base_url}{path}"
        hdrs = self._headers(headers)
        query = self._encode_params(params)

        for attempt in range(attempts):
            try:
                resp = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=hdrs,
                    json=json_body,
                    params=query,
                    timeout=timeout,
                )
                if resp.ok:
                    ctype = resp.headers.get("Content-Type", "").split(";")[0].strip()
                    logger.debug("HTTP %s %s %s", method, url, resp.status_code)
                    if ctype in ("application/json", "text/json", "application/problem+json"):
                        try:
                            return resp.json()
                        except ValueError as e:
                            raise JSONDecodeError(str(e)) from e
                    return resp.content

                if attempt < attempts - 1:
                    backoff = sleep_non_200 * (2 ** attempt)
                    time.sleep(backoff)
                    continue

                message = {
                    "url": url,
                    "status_code": resp.status_code,
                    "response_text": resp.text[:1000],
                    "headers": self._redact_headers(hdrs),
                    "json_body": json_body,
                    "params": query,
                }
                msg = json.dumps(message, ensure_ascii=False)
                exc_cls = ClientError if 400 <= resp.status_code < 500 else ServerError
                raise exc_cls(
                    status_code=resp.status_code,
                    method=method,
                    url=url,
                    message=msg,
                    request_headers=self._redact_headers(hdrs),
                    request_params=query,
                    request_body=dict(json_body) if json_body else None,
                    response_text=resp.text[:2000],
                    correlation_id=hdrs.get("x-correlation-id"),
                )

            except requests.exceptions.Timeout as e:
                if attempt < attempts - 1:
                    backoff = sleep_timeout * (2 ** attempt)
                    time.sleep(backoff)
                    continue
                raise TimeoutError(f"Timeout calling {method} {url}") from e
            except requests.exceptions.RequestException as e:
                if attempt < attempts - 1:
                    time.sleep(0.5 * (2 ** attempt))
                    continue
                raise NetworkError(f"Network error calling {method} {url}: {e}") from e
