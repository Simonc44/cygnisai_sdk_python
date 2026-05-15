"""
CygnisAI Python SDK
~~~~~~~~~~~~~~~~~~~

Simple, fast access to CygnisAI language models.

Quick-start::

    import cygnisai_sdk_python as cygnis

    cygnis.configure(api_key="YOUR_KEY")
    model = cygnis.GenerativeModel("alpha2")
    response = model.generate_content("Give me a Python tip.")
    print(response.text)

Streaming::

    stream = model.generate_content("Tell me a story.", stream=True)
    async for token in stream:
        print(token, end="", flush=True)
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, AsyncGenerator, List, Optional

from .client import (
    AuthenticationError,
    CygnisAIClient,
    CygnisAIError,
    NetworkError,
    RateLimitError,
    ResponseValidationError,
    ServerError,
)
from .models import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    Message,
    Role,
    UsageInfo,
)

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

_global_client: Optional[CygnisAIClient] = None
_global_api_key: Optional[str] = None
_global_base_url: str = "https://needlessly-faithful-gopher.ngrok-free.app"


# ---------------------------------------------------------------------------
# High-level response wrappers
# ---------------------------------------------------------------------------

class GenerativeResponse:
    """Wraps a completed :class:`~cygnisai_sdk_python.models.ChatResponse`."""

    def __init__(self, text: str, full_response: Optional[ChatResponse] = None) -> None:
        self.text = text
        self._full_response = full_response

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        snippet = self.text[:60].replace("\n", " ")
        return f"GenerativeResponse(text={snippet!r})"

    @property
    def full_response(self) -> Optional[ChatResponse]:
        """The raw :class:`~cygnisai_sdk_python.models.ChatResponse`, if available."""
        return self._full_response

    @property
    def usage(self) -> Optional[UsageInfo]:
        """Token-usage statistics, if available."""
        return self._full_response.usage if self._full_response else None

    @property
    def latency_ms(self) -> Optional[int]:
        """Round-trip latency reported by the API."""
        return self._full_response.latency_ms if self._full_response else None


class GenerativeStreamResponse:
    """Wraps an async token generator from :meth:`CygnisAIClient.chat_stream`."""

    def __init__(self, async_generator: AsyncGenerator[str, None]) -> None:
        self._async_generator = async_generator

    def __aiter__(self):
        return self._async_generator.__aiter__()


# ---------------------------------------------------------------------------
# GenerativeModel
# ---------------------------------------------------------------------------

class GenerativeModel:
    """
    High-level interface for a CygnisAI language model.

    Uses the global client configured via :func:`configure`.

    Example::

        model = GenerativeModel("alpha2")
        response = model.generate_content("Hello!")
        print(response.text)
    """

    def __init__(self, model_name: str) -> None:
        if not model_name:
            raise ValueError("model_name must not be empty.")
        self.model_name = model_name

    def _get_client(self) -> CygnisAIClient:
        if _global_client is None:
            raise CygnisAIError(
                "CygnisAI client is not configured. "
                "Call cygnis.configure(api_key='YOUR_KEY') first."
            )
        return _global_client

    def generate_content(
        self,
        prompt: str,
        messages: Optional[List[Message]] = None,
        stream: bool = False,
    ) -> Any:
        """
        Generate text from a prompt.

        Args:
            prompt: The question or instruction for the model.
            messages: Optional conversation history.
            stream: If ``True``, returns a :class:`GenerativeStreamResponse`
                    that you can ``async for`` over.

        Returns:
            :class:`GenerativeResponse` (blocking) or
            :class:`GenerativeStreamResponse` (streaming).
        """
        client = self._get_client()
        request = ChatRequest(
            model=self.model_name,
            prompt=prompt,
            messages=messages,
            stream=stream,
        )

        if stream:
            return GenerativeStreamResponse(client.chat_stream(request=request))

        # Synchronous execution via asyncio.run — works in scripts & notebooks
        async def _run() -> ChatResponse:
            return await client.chat(request=request)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Inside an async context (e.g. Jupyter) — caller must await
            raise RuntimeError(
                "generate_content() cannot be called synchronously inside a running "
                "event loop. Use `await model.async_generate_content(...)` instead, "
                "or call it from a regular (non-async) context."
            )

        full_response = asyncio.run(_run())
        return GenerativeResponse(text=full_response.response, full_response=full_response)

    async def async_generate_content(
        self,
        prompt: str,
        messages: Optional[List[Message]] = None,
        stream: bool = False,
    ) -> Any:
        """
        Async version of :meth:`generate_content` for use inside ``async`` code.

        Example::

            response = await model.async_generate_content("Hello!")
        """
        client = self._get_client()
        request = ChatRequest(
            model=self.model_name,
            prompt=prompt,
            messages=messages,
            stream=stream,
        )

        if stream:
            return GenerativeStreamResponse(client.chat_stream(request=request))

        full_response = await client.chat(request=request)
        return GenerativeResponse(text=full_response.response, full_response=full_response)


# ---------------------------------------------------------------------------
# configure()
# ---------------------------------------------------------------------------

def configure(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> None:
    """
    Initialise the global CygnisAI client.

    Call this once at startup before using :class:`GenerativeModel`.

    Args:
        api_key: Your CygnisAI API key. Falls back to the ``CYGNIS_API_KEY``
                 environment variable if not provided.
        base_url: Override the default API base URL.
        timeout: HTTP timeout in seconds (default 30).
        max_retries: Number of automatic retries on transient errors (default 3).

    Raises:
        ValueError: If no API key is found.
    """
    global _global_client, _global_api_key, _global_base_url

    resolved_key = api_key or os.environ.get("CYGNIS_API_KEY")
    if not resolved_key:
        raise ValueError(
            "No API key provided. Pass api_key= or set the CYGNIS_API_KEY "
            "environment variable."
        )

    _global_api_key = resolved_key
    if base_url:
        _global_base_url = base_url

    # Cleanly close the previous client if one exists
    if _global_client is not None:
        try:
            asyncio.run(_global_client.close())
        except RuntimeError:
            pass  # Already inside a running loop — leak is acceptable here

    _global_client = CygnisAIClient(
        api_key=_global_api_key,
        base_url=_global_base_url,
        timeout=timeout,
        max_retries=max_retries,
    )


# ---------------------------------------------------------------------------
# Public API surface
# ---------------------------------------------------------------------------

__all__ = [
    # Configuration
    "configure",
    # High-level interface
    "GenerativeModel",
    "GenerativeResponse",
    "GenerativeStreamResponse",
    # Data models
    "Message",
    "Role",
    "UsageInfo",
    "ChatRequest",
    "ChatResponse",
    "ErrorResponse",
    # Exceptions
    "CygnisAIError",
    "AuthenticationError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    "ResponseValidationError",
    # Low-level client (advanced use)
    "CygnisAIClient",
]