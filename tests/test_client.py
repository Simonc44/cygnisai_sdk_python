"""
Tests for the CygnisAI Python SDK.
Run with: pytest tests/ -v
"""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from cygnisai_sdk_python import (
    AuthenticationError,
    CygnisAIClient,
    CygnisAIError,
    ChatRequest,
    Message,
    NetworkError,
    RateLimitError,
    ResponseValidationError,
    Role,
    ServerError,
)
from cygnisai_sdk_python.models import ChatResponse, UsageInfo


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_API_KEY = "test-api-key-123"
MOCK_BASE_URL = "http://test-api.cygnisai.com"

VALID_RESPONSE = {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "response": "This is a test reply.",
    "latency_ms": 42,
    "redacted": False,
    "usage": {"prompt_tokens": 5, "completion_tokens": 8, "total_tokens": 13},
}

STREAM_LINES = [
    'data: {"response": "Hello"}\n',
    'data: {"response": " world"}\n',
    'data: {"response": "!"}\n',
    "data: [DONE]\n",
]


@pytest.fixture
def mock_client(mock_base_url=MOCK_BASE_URL):
    return CygnisAIClient(api_key=MOCK_API_KEY, base_url=mock_base_url)


@pytest.fixture
def basic_request():
    return ChatRequest(
        model="alpha2",
        prompt="Hello!",
        messages=[Message(role=Role.USER, content="Hi")],
    )


# ---------------------------------------------------------------------------
# Model unit tests
# ---------------------------------------------------------------------------

class TestModels:
    def test_message_valid_roles(self):
        for role in ("user", "assistant", "system"):
            m = Message(role=role, content="text")
            assert m.role == role

    def test_message_empty_content_fails(self):
        with pytest.raises(Exception):
            Message(role="user", content="")

    def test_chat_request_empty_messages_becomes_none(self):
        req = ChatRequest(model="alpha2", prompt="hi", messages=[])
        assert req.messages is None

    def test_chat_response_parses_usage(self):
        resp = ChatResponse(**VALID_RESPONSE)
        assert isinstance(resp.usage, UsageInfo)
        assert resp.usage.total_tokens == 13

    def test_chat_response_usage_dict_passthrough(self):
        """Extra keys in usage must not cause a validation error."""
        data = {**VALID_RESPONSE, "usage": {"total_tokens": 5, "custom_key": "x"}}
        resp = ChatResponse(**data)
        assert resp.usage.total_tokens == 5


# ---------------------------------------------------------------------------
# CygnisAIClient – non-streaming
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chat_success(mock_client, basic_request, httpx_mock):
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/v3/chat",
        method="POST",
        json=VALID_RESPONSE,
        status_code=200,
    )
    resp = await mock_client.chat(basic_request)
    assert isinstance(resp, ChatResponse)
    assert resp.response == VALID_RESPONSE["response"]
    assert str(resp.id) == VALID_RESPONSE["id"]


@pytest.mark.asyncio
async def test_chat_forces_stream_false(mock_client, basic_request, httpx_mock):
    """chat() must always send stream=False regardless of request."""
    basic_request.stream = True
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/v3/chat",
        method="POST",
        json=VALID_RESPONSE,
        status_code=200,
    )
    await mock_client.chat(basic_request)
    sent = httpx_mock.get_request()
    body = json.loads(sent.content)
    assert body.get("stream") is False


@pytest.mark.asyncio
async def test_chat_400_raises_cygnis_error(mock_client, basic_request, httpx_mock):
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/v3/chat",
        method="POST",
        json={"detail": "Bad request"},
        status_code=400,
    )
    with pytest.raises(CygnisAIError) as exc_info:
        await mock_client.chat(basic_request)
    assert exc_info.value.status_code == 400
    assert "Bad request" in exc_info.value.message


@pytest.mark.asyncio
async def test_chat_401_raises_authentication_error(mock_client, basic_request, httpx_mock):
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/v3/chat",
        method="POST",
        json={"detail": "Unauthorized"},
        status_code=401,
    )
    with pytest.raises(AuthenticationError):
        await mock_client.chat(basic_request)


@pytest.mark.asyncio
async def test_chat_429_raises_rate_limit_error(mock_client, basic_request, httpx_mock):
    # First call returns 429, then 200 (retry succeeds)
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/v3/chat",
        method="POST",
        json={"detail": "Too many requests"},
        status_code=429,
    )
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/v3/chat",
        method="POST",
        json=VALID_RESPONSE,
        status_code=200,
    )
    # With retries=1 the second call should succeed
    client = CygnisAIClient(api_key=MOCK_API_KEY, base_url=MOCK_BASE_URL, max_retries=1)
    resp = await client.chat(basic_request)
    assert isinstance(resp, ChatResponse)


@pytest.mark.asyncio
async def test_chat_500_raises_server_error(mock_client, basic_request, httpx_mock):
    for _ in range(mock_client.max_retries + 1):
        httpx_mock.add_response(
            url=f"{MOCK_BASE_URL}/v3/chat",
            method="POST",
            json={"detail": "Internal server error"},
            status_code=500,
        )
    with pytest.raises(ServerError):
        await mock_client.chat(basic_request)


@pytest.mark.asyncio
async def test_chat_invalid_response_raises_validation_error(
    mock_client, basic_request, httpx_mock
):
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/v3/chat",
        method="POST",
        json={"unexpected": "schema"},
        status_code=200,
    )
    with pytest.raises(ResponseValidationError):
        await mock_client.chat(basic_request)


# ---------------------------------------------------------------------------
# CygnisAIClient – streaming
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chat_stream_success(mock_client, basic_request, httpx_mock):
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/v3/chat",
        method="POST",
        content="".join(STREAM_LINES).encode(),
        status_code=200,
    )
    basic_request.stream = True
    tokens = []
    async for token in mock_client.chat_stream(basic_request):
        tokens.append(token)
    assert "".join(tokens) == "Hello world!"


@pytest.mark.asyncio
async def test_chat_stream_500_raises_server_error(mock_client, basic_request, httpx_mock):
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/v3/chat",
        method="POST",
        json={"detail": "Internal error"},
        status_code=500,
    )
    basic_request.stream = True
    with pytest.raises(ServerError):
        async for _ in mock_client.chat_stream(basic_request):
            pass


@pytest.mark.asyncio
async def test_chat_stream_error_in_stream_body(mock_client, basic_request, httpx_mock):
    """Errors embedded in the SSE stream should raise CygnisAIError."""
    error_stream = 'data: {"error": "Model overloaded"}\n'
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/v3/chat",
        method="POST",
        content=error_stream.encode(),
        status_code=200,
    )
    basic_request.stream = True
    with pytest.raises(CygnisAIError) as exc_info:
        async for _ in mock_client.chat_stream(basic_request):
            pass
    assert "Model overloaded" in exc_info.value.message


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_client_context_manager_closes():
    client = CygnisAIClient(api_key=MOCK_API_KEY, base_url=MOCK_BASE_URL)
    async with client:
        assert not client._client.is_closed
    assert client._client.is_closed


@pytest.mark.asyncio
async def test_client_close():
    client = CygnisAIClient(api_key=MOCK_API_KEY, base_url=MOCK_BASE_URL)
    await client.close()
    assert client._client.is_closed
    # Calling close() again should be safe
    await client.close()


# ---------------------------------------------------------------------------
# constructor validation
# ---------------------------------------------------------------------------

def test_client_empty_api_key_raises():
    with pytest.raises(ValueError):
        CygnisAIClient(api_key="", base_url=MOCK_BASE_URL)


def test_chat_request_empty_prompt_raises():
    with pytest.raises(Exception):
        ChatRequest(model="alpha2", prompt="")


def test_chat_request_empty_model_raises():
    with pytest.raises(Exception):
        ChatRequest(model="", prompt="hello")