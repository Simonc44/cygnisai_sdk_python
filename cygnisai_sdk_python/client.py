"""
CygnisAI SDK - Async HTTP Client
Handles authentication, serialisation, error mapping, retries and streaming.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Optional

import httpx
from pydantic import ValidationError

from .models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class CygnisAIError(Exception):
    """Base exception for all CygnisAI SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_details = error_details

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r})"
        )


class AuthenticationError(CygnisAIError):
    """Raised on HTTP 401 / 403."""


class RateLimitError(CygnisAIError):
    """Raised on HTTP 429."""


class ServerError(CygnisAIError):
    """Raised on HTTP 5xx."""


class NetworkError(CygnisAIError):
    """Raised when the request never reaches the server."""


class ResponseValidationError(CygnisAIError):
    """Raised when the API response doesn't match the expected schema."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_STATUS_EXCEPTION_MAP: dict[int, type[CygnisAIError]] = {
    401: AuthenticationError,
    403: AuthenticationError,
    429: RateLimitError,
}


def _map_status_error(status_code: int, message: str, details: Any) -> CygnisAIError:
    exc_cls = _STATUS_EXCEPTION_MAP.get(
        status_code,
        ServerError if status_code >= 500 else CygnisAIError,
    )
    return exc_cls(message, status_code=status_code, error_details=details)


def _extract_error_message(body: dict[str, Any]) -> str:
    return (
        body.get("detail")
        or body.get("message")
        or body.get("error")
        or str(body)
    )


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://needlessly-faithful-gopher.ngrok-free.app"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class CygnisAIClient:
    """
    Async HTTP client for the CygnisAI API.

    Can be used as an async context manager::

        async with CygnisAIClient(api_key="...") as client:
            response = await client.chat(request)

    Or managed manually::

        client = CygnisAIClient(api_key="...")
        try:
            ...
        finally:
            await client.close()
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        **httpx_kwargs: Any,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty.")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max(0, max_retries)

        default_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "cygnisai-python-sdk/1.0.0",
        }
        headers = {**default_headers, **httpx_kwargs.pop("headers", {})}

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=headers,
            **httpx_kwargs,
        )

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "CygnisAIClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        if not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Internal: retry logic
    # ------------------------------------------------------------------

    async def _post_with_retry(
        self,
        path: str,
        payload: dict[str, Any],
    ) -> httpx.Response:
        """POST *path* with exponential-backoff retries on transient errors."""
        import asyncio

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = await self._client.post(path, json=payload)
                if resp.status_code not in _RETRY_STATUS_CODES or attempt == self.max_retries:
                    return resp
                wait = 2 ** attempt
                logger.warning(
                    "CygnisAI: HTTP %s on attempt %d/%d — retrying in %ds",
                    resp.status_code, attempt + 1, self.max_retries + 1, wait,
                )
                await asyncio.sleep(wait)
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt == self.max_retries:
                    break
                wait = 2 ** attempt
                logger.warning(
                    "CygnisAI: Network error on attempt %d/%d — retrying in %ds: %s",
                    attempt + 1, self.max_retries + 1, wait, exc,
                )
                await asyncio.sleep(wait)

        raise NetworkError(
            f"Request failed after {self.max_retries + 1} attempts: {last_exc}",
            error_details=str(last_exc),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Send a chat request and return the complete response.

        Args:
            request: A :class:`~cygnisai_sdk_python.models.ChatRequest` instance.

        Returns:
            :class:`~cygnisai_sdk_python.models.ChatResponse`

        Raises:
            AuthenticationError: On 401/403.
            RateLimitError: On 429.
            ServerError: On 5xx.
            NetworkError: On connection failure.
            ResponseValidationError: If the response body doesn't match the schema.
            CygnisAIError: For any other API error.
        """
        request.stream = False
        payload = request.model_dump(exclude_none=True)

        try:
            raw = await self._post_with_retry("/v3/chat", payload)
        except NetworkError:
            raise

        if raw.status_code != 200:
            try:
                body = raw.json()
                msg = _extract_error_message(body)
            except Exception:
                body = {}
                msg = raw.text
            raise _map_status_error(
                raw.status_code,
                f"API error (HTTP {raw.status_code}): {msg}",
                body,
            )

        try:
            return ChatResponse(**raw.json())
        except (ValidationError, Exception) as exc:
            raise ResponseValidationError(
                f"Failed to parse API response: {exc}",
                error_details=str(exc),
            ) from exc

    async def chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        Send a chat request and yield tokens as they arrive (SSE).

        Args:
            request: A :class:`~cygnisai_sdk_python.models.ChatRequest` instance.

        Yields:
            str – individual text tokens from the model.

        Raises:
            CygnisAIError (and subclasses): as documented on :meth:`chat`.
        """
        request.stream = True
        payload = request.model_dump(exclude_none=True)

        async with self._client.stream("POST", "/v3/chat", json=payload) as response:
            if response.status_code != 200:
                error_bytes = await response.aread()
                try:
                    body = json.loads(error_bytes.decode())
                    msg = _extract_error_message(body)
                except Exception:
                    body = {}
                    msg = error_bytes.decode()
                raise _map_status_error(
                    response.status_code,
                    f"API error (HTTP {response.status_code}): {msg}",
                    body,
                )

            async for raw_line in response.aiter_lines():
                line = raw_line.strip()
                if not line:
                    continue

                if line.startswith("data:"):
                    content = line[5:].strip()

                    if content == "[DONE]":
                        return

                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError:
                        # Yield raw text if it isn't valid JSON
                        yield content
                        continue

                    if not isinstance(data, dict):
                        yield str(data)
                        continue

                    # Surface server-side errors embedded in the stream
                    if "error" in data or "detail" in data:
                        err_key = "error" if "error" in data else "detail"
                        err_val = data[err_key]
                        if isinstance(err_val, list):
                            msgs = [
                                f"{e.get('loc', ['?'])[-1]}: {e.get('msg', '')}"
                                for e in err_val
                                if isinstance(e, dict)
                            ]
                            err_val = "; ".join(msgs)
                        raise CygnisAIError(
                            f"Server error in stream: {err_val}",
                            error_details=data,
                        )

                    token = data.get("response") or data.get("text") or ""
                    if token:
                        yield token