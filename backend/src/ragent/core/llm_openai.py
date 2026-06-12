"""OpenAI-compatible LLM Provider implementation."""

from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel

from ragent.core.llm import LLMProvider
from ragent.core.types import LLMMessage, LLMResponse, ProviderConfig


class OpenAIChatCompletionRequest(BaseModel):
    model: str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False


class OpenAIChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, int] | None = None


class OpenAILLMProvider(LLMProvider):
    """OpenAI-compatible LLM provider (OpenAI, Azure, DashScope, etc.)."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client = httpx.AsyncClient(
            base_url=config.base_url or "https://api.openai.com/v1",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=config.timeout,
        )

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        """Convert internal message format to OpenAI format."""
        result = []
        for msg in messages:
            if msg.role == "tool":
                result.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id,
                })
            elif msg.tool_calls:
                result.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                })
            else:
                result.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        return result

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        request = OpenAIChatCompletionRequest(
            model=self.config.model,
            messages=self._convert_messages(messages),
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.post(
                    "/chat/completions",
                    json=request.model_dump(exclude_none=True),
                )
                response.raise_for_status()
                data = OpenAIChatCompletionResponse(**response.json())

                choice = data.choices[0]
                message = choice.get("message", {})

                return LLMResponse(
                    content=message.get("content"),
                    tool_calls=message.get("tool_calls"),
                    usage=data.usage,
                    model=data.model,
                    finish_reason=choice.get("finish_reason"),
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.config.max_retries - 1:
                    continue
                raise
            except Exception:
                if attempt < self.config.max_retries - 1:
                    continue
                raise

        raise RuntimeError("Max retries exceeded")

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ):
        request = OpenAIChatCompletionRequest(
            model=self.config.model,
            messages=self._convert_messages(messages),
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async with self._client.stream(
            "POST",
            "/chat/completions",
            json=request.model_dump(exclude_none=True),
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    if content := delta.get("content"):
                        yield content
                except json.JSONDecodeError:
                    continue

    @property
    def model_name(self) -> str:
        return self.config.model

    def supports_vision(self) -> bool:
        return "gpt-4" in self.config.model.lower() or "vision" in self.config.model.lower()

    async def close(self) -> None:
        await self._client.aclose()