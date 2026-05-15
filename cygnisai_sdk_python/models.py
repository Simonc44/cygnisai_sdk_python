"""
CygnisAI SDK - Data Models
Pydantic v2 models for request/response validation.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
import uuid

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Role(str, Enum):
    """Valid message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

class Message(BaseModel):
    """A single turn in a conversation."""

    role: Role = Field(..., description="Author role: 'user', 'assistant', or 'system'.")
    content: str = Field(..., min_length=1, description="Text content of the message.")

    model_config = {"use_enum_values": True}


class UsageInfo(BaseModel):
    """Token-usage breakdown returned by the API."""

    prompt_tokens: Optional[int] = Field(None, ge=0)
    completion_tokens: Optional[int] = Field(None, ge=0)
    total_tokens: Optional[int] = Field(None, ge=0)

    # Keep extra fields from the API without failing validation
    model_config = {"extra": "allow"}


class ChatRequest(BaseModel):
    """Payload sent to POST /v3/chat."""

    model: str = Field(..., min_length=1, description="Model name, e.g. 'alpha2'.")
    prompt: str = Field(..., min_length=1, description="User prompt / question.")
    messages: Optional[List[Message]] = Field(
        None, description="Conversation history (optional)."
    )
    stream: bool = Field(False, description="Enable SSE streaming.")

    @field_validator("messages", mode="before")
    @classmethod
    def _messages_not_empty_list(cls, v: Any) -> Any:
        if isinstance(v, list) and len(v) == 0:
            return None
        return v


class ChatResponse(BaseModel):
    """Successful non-streaming response from POST /v3/chat."""

    id: uuid.UUID = Field(..., description="Unique response identifier.")
    response: str = Field(..., description="Full model reply.")
    latency_ms: int = Field(..., ge=0, description="Round-trip latency in milliseconds.")
    redacted: bool = Field(..., description="Whether the reply was moderated.")
    usage: UsageInfo = Field(..., description="Token-usage statistics.")

    @field_validator("usage", mode="before")
    @classmethod
    def _coerce_usage(cls, v: Any) -> Any:
        if isinstance(v, dict):
            return UsageInfo(**v)
        return v


# ---------------------------------------------------------------------------
# Error model
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Individual validation-error entry (FastAPI style)."""

    loc: List[str] = Field(default_factory=list)
    msg: str = ""
    type: str = ""


class ErrorResponse(BaseModel):
    """Standardised error envelope returned by the API."""

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error message.")
    details: Optional[List[ErrorDetail]] = Field(
        None, description="Validation details when applicable."
    )