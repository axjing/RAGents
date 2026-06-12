"""Core type definitions for Ragent."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DocType(str, Enum):
    """Document type enumeration."""

    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"


class Chunk(BaseModel):
    """A chunk of content from a document."""

    id: UUID
    document_id: UUID
    doc_type: DocType
    text: str | None = None
    media_ref: str | None = None
    page: int | None = None
    span: tuple[int, int] | None = None
    embedding: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """A tool invocation with its result."""

    tool_name: str
    arguments: dict[str, Any]
    observation: str | None = None
    citations: list[UUID] = Field(default_factory=list)
    ts: datetime = Field(default_factory=datetime.utcnow)


class AgentTrace(BaseModel):
    """A single step in an agent's reasoning trace."""

    step: int
    thought: str
    tool_call: ToolCall | None = None
    reflection: str | None = None


class ChatTurn(BaseModel):
    """A complete chat interaction turn."""

    user_query: str
    multimodal_inputs: list[Any] = Field(default_factory=list)
    plan_dag: dict[str, Any] | None = None
    traces: list[AgentTrace] = Field(default_factory=list)
    answer: str | None = None
    citations: list[Chunk] = Field(default_factory=list)


class LLMMessage(BaseModel):
    """A message in an LLM conversation."""

    role: str  # system, user, assistant, tool
    content: str | list[dict[str, Any]]  # Support multimodal content
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class LLMResponse(BaseModel):
    """Response from an LLM provider."""

    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    usage: dict[str, int] | None = None
    model: str | None = None
    finish_reason: str | None = None


class EmbeddingResponse(BaseModel):
    """Response from an embedding provider."""

    embeddings: list[list[float]]
    usage: dict[str, int] | None = None
    model: str | None = None


class ProviderConfig(BaseModel):
    """Base configuration for providers."""

    model: str
    api_key: str | None = None
    base_url: str | None = None
    timeout: float = 30.0
    max_retries: int = 3
    extra: dict[str, Any] = Field(default_factory=dict)