"""Chat API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any

router = APIRouter()


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    session_id: str | None = None
    multimodal_inputs: list[dict[str, Any]] = Field(default_factory=list)
    stream: bool = False


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    traces: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Chat with the agent."""
    # TODO: Implement actual chat logic with agent
    return ChatResponse(
        session_id=request.session_id or "new-session",
        answer="Hello! I'm the Ragent agent. This is a placeholder response.",
        citations=[],
        traces=[],
    )


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Stream chat response."""
    # TODO: Implement streaming
    from fastapi.responses import StreamingResponse

    async def generate():
        yield "data: Hello! This is a streaming placeholder.\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")