"""Custom exception types for the Mallsense SDK.

These classes provide structured error information suitable for robust
error handling and logging in production systems.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class MallsenseError(Exception):
    """Base class for all SDK errors."""


class NetworkError(MallsenseError):
    """Raised when a low-level network error occurs (DNS, connection)."""


class TimeoutError(MallsenseError):
    """Raised when a request exceeds the configured timeout."""


class JSONDecodeError(MallsenseError):
    """Raised when a response is not valid JSON when JSON was expected."""


class HTTPError(MallsenseError):
    """HTTP error with context about the request and response."""

    def __init__(
        self,
        *,
        status_code: int,
        method: str,
        url: str,
        message: str,
        request_headers: Optional[Dict[str, Any]] = None,
        request_params: Optional[Dict[str, Any]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        response_text: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.method = method
        self.url = url
        self.request_headers = request_headers or {}
        self.request_params = request_params or {}
        self.request_body = request_body or {}
        self.response_text = response_text
        self.correlation_id = correlation_id

    def __str__(self) -> str:
        cid = f" cid={self.correlation_id}" if self.correlation_id else ""
        return f"HTTPError {self.status_code} {self.method} {self.url}{cid}: {super().__str__()}"


class ClientError(HTTPError):
    """4xx error from the server (invalid input, not found, etc.)."""


class ServerError(HTTPError):
    """5xx error from the server (temporary/unexpected issues)."""


# More specific client-side errors for common status codes
class UnauthorizedError(ClientError):
    """401 Unauthorized"""


class ForbiddenError(ClientError):
    """403 Forbidden"""


class NotFoundError(ClientError):
    """404 Not Found"""


class ConflictError(ClientError):
    """409 Conflict"""


class UnprocessableEntityError(ClientError):
    """422 Unprocessable Entity"""


class TooManyRequestsError(ClientError):
    """429 Too Many Requests"""
