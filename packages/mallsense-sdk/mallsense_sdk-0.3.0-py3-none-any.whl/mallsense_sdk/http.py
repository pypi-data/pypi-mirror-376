from __future__ import annotations

"""HTTP client utilities for the Mallsense SDK.

Provides a robust request wrapper with a shared Session (connection pooling),
retries with jitter and 429 handling, structured exceptions, parameter encoding,
and optional correlation IDs. Exposes a streaming API and a simple paginator.
"""

import json
import logging
import random
import time
import uuid
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Generator, Iterable, Mapping, MutableMapping, Optional, Union

import requests
from requests.adapters import HTTPAdapter

from .exceptions import (
    ClientError,
    ServerError,
    TimeoutError,
    NetworkError,
    JSONDecodeError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    UnprocessableEntityError,
    TooManyRequestsError,
)


Headers = Mapping[str, str]
ParamsValue = Union[str, int, float, bool, None]
Params = MutableMapping[str, ParamsValue]


logger = logging.getLogger("mallsense_sdk")

try:
    from opentelemetry import trace as ot_trace  # type: ignore
    _OTEL_TRACER = ot_trace.get_tracer("mallsense_sdk.http")
except Exception:  # pragma: no cover - optional dependency
    _OTEL_TRACER = None


class HTTPApi:
    """Small HTTP client wrapper with retries and helpful errors.

    - Adds x-token/x-app-key headers
    - Encodes list-like query params as comma-separated values (CSV)
    - Retries timeouts and non-2xx with exponential backoff
    - Raises structured exceptions with request/response context
    """

    def __init__(
        self,
        token: str,
        app_key: str,
        base_url: str,
        *,
        verify: Union[bool, str, None] = None,
        cert: Optional[Union[str, tuple[str, str]]] = None,
        proxies: Optional[Mapping[str, str]] = None,
        pool_connections: int = 10,
        pool_maxsize: int = 50,
    ):
        self.token = token
        self.app_key = app_key
        self.base_url = base_url.rstrip("/")
        self.verify = verify
        self.cert = cert
        self.proxies = dict(proxies) if proxies else None

        # Shared Session with tuned connection pool
        self._session = requests.Session()
        adapter = HTTPAdapter(pool_connections=pool_connections, pool_maxsize=pool_maxsize)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

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

        # Idempotency-aware retry policy
        method_up = method.upper()
        idempotent = method_up in ("GET", "HEAD", "OPTIONS")
        has_idempotency_key = "Idempotency-Key" in hdrs
        effective_attempts = attempts if (idempotent or has_idempotency_key) else 1

        def _jitter(base: float, attempt_i: int) -> float:
            return base * (2 ** attempt_i) + random.uniform(0, base)

        for attempt in range(effective_attempts):
            try:
                span_cm = (
                    _OTEL_TRACER.start_as_current_span(f"HTTP {method_up}") if _OTEL_TRACER else None
                )
                if span_cm:
                    span = span_cm.__enter__()
                    try:
                        span.set_attribute("http.method", method_up)
                        span.set_attribute("http.url", url)
                    except Exception:
                        pass
                resp = self._session.request(
                    method=method.upper(),
                    url=url,
                    headers=hdrs,
                    json=json_body,
                    params=query,
                    timeout=timeout,
                    verify=self.verify if self.verify is not None else True,
                    cert=self.cert,
                    proxies=self.proxies,
                )
                if resp.ok:
                    if span_cm:
                        try:
                            span.set_attribute("http.status_code", resp.status_code)
                        except Exception:
                            pass
                        span_cm.__exit__(None, None, None)
                    ctype = resp.headers.get("Content-Type", "").split(";")[0].strip()
                    logger.debug("HTTP %s %s %s", method, url, resp.status_code)
                    if ctype in ("application/json", "text/json", "application/problem+json"):
                        try:
                            return resp.json()
                        except ValueError as e:
                            raise JSONDecodeError(str(e)) from e
                    return resp.content

                # Handle 429 with Retry-After
                if resp.status_code == 429 and attempt < effective_attempts - 1:
                    ra = resp.headers.get("Retry-After")
                    delay = None
                    if ra:
                        try:
                            # Numeric seconds
                            delay = float(ra)
                        except ValueError:
                            # HTTP-date
                            try:
                                dt = parsedate_to_datetime(ra)
                                delay = max(0.0, (dt - datetime.utcnow()).total_seconds())
                            except Exception:
                                delay = None
                    time.sleep(delay if delay is not None else _jitter(sleep_non_200, attempt))
                    continue

                if attempt < effective_attempts - 1:
                    time.sleep(_jitter(sleep_non_200, attempt))
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
                # Map specific 4xx to specialized exceptions
                if 400 <= resp.status_code < 500:
                    mapping = {
                        401: UnauthorizedError,
                        403: ForbiddenError,
                        404: NotFoundError,
                        409: ConflictError,
                        422: UnprocessableEntityError,
                        429: TooManyRequestsError,
                    }
                    exc_cls = mapping.get(resp.status_code, ClientError)
                else:
                    exc_cls = ServerError
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
                if attempt < effective_attempts - 1:
                    time.sleep(_jitter(sleep_timeout, attempt))
                    continue
                raise TimeoutError(f"Timeout calling {method} {url}") from e
            except requests.exceptions.RequestException as e:
                if attempt < effective_attempts - 1:
                    time.sleep(_jitter(0.5, attempt))
                    continue
                raise NetworkError(f"Network error calling {method} {url}: {e}") from e
            finally:
                if span_cm:
                    try:
                        span_cm.__exit__(None, None, None)
                    except Exception:
                        pass

    def stream(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Headers] = None,
        params: Optional[Mapping[str, Any]] = None,
        timeout: float = 60.0,
        chunk_size: int = 8192,
    ) -> Generator[bytes, None, None]:
        """Stream a response body in chunks.

        Yields bytes chunks. Raises the same structured exceptions on errors.
        """
        url = f"{self.base_url}{path}"
        hdrs = self._headers(headers)
        query = self._encode_params(params)
        try:
            with self._session.request(
                method=method.upper(),
                url=url,
                headers=hdrs,
                params=query,
                timeout=timeout,
                stream=True,
                verify=self.verify if self.verify is not None else True,
                cert=self.cert,
                proxies=self.proxies,
            ) as resp:
                if not resp.ok:
                    message = {
                        "url": url,
                        "status_code": resp.status_code,
                        "response_text": resp.text[:1000],
                        "headers": self._redact_headers(hdrs),
                        "params": query,
                    }
                    msg = json.dumps(message, ensure_ascii=False)
                    if 400 <= resp.status_code < 500:
                        mapping = {
                            401: UnauthorizedError,
                            403: ForbiddenError,
                            404: NotFoundError,
                            409: ConflictError,
                            422: UnprocessableEntityError,
                            429: TooManyRequestsError,
                        }
                        exc_cls = mapping.get(resp.status_code, ClientError)
                    else:
                        exc_cls = ServerError
                    raise exc_cls(
                        status_code=resp.status_code,
                        method=method,
                        url=url,
                        message=msg,
                        request_headers=self._redact_headers(hdrs),
                        request_params=query,
                        response_text=resp.text[:2000],
                        correlation_id=hdrs.get("x-correlation-id"),
                    )
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        yield chunk
        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Timeout calling {method} {url}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error calling {method} {url}: {e}") from e

    def paginate(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        page_size: int = 1000,
        max_pages: Optional[int] = None,
    ) -> Iterable[Any]:
        """Simple offset/limit paginator yielding list items from array endpoints."""
        base_params: Dict[str, Any] = dict(params or {})
        offset = int(base_params.get("offset") or 0)
        page_size = int(base_params.get("limit") or page_size)
        pages = 0
        while True:
            q = dict(base_params)
            q["limit"] = page_size
            q["offset"] = offset
            data = self.request("GET", path, params=q)
            if not isinstance(data, list):
                # if server wraps list in object, try 'results'
                data = data.get("results", []) if isinstance(data, dict) else []
            if not data:
                break
            for item in data:
                yield item
            offset += page_size
            pages += 1
            if max_pages is not None and pages >= max_pages:
                break
