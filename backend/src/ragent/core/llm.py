"""LLM Provider abstraction for Ragent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ragent.core.types import LLMMessage, LLMResponse, ProviderConfig


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a chat completion."""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ):
        """Generate a streaming chat completion."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        ...

    def supports_tools(self) -> bool:
        """Check if provider supports native tool calling."""
        return True

    def supports_vision(self) -> bool:
        """Check if provider supports vision/multimodal input."""
        return False


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing without API keys."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._responses: list[LLMResponse] = []
        self._call_count = 0

    def add_response(self, response: LLMResponse) -> None:
        """Add a canned response for testing."""
        self._responses.append(response)

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        if self._responses:
            response = self._responses[self._call_count % len(self._responses)]
            self._call_count += 1
            return response
        return LLMResponse(
            content="Mock response",
            model=self.config.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ):
        response = await self.chat(messages, tools, tool_choice, temperature, max_tokens, **kwargs)
        if response.content:
            for chunk in response.content.split():
                yield chunk + " "

    @property
    def model_name(self) -> str:
        return self.config.model


def create_llm_provider(config: ProviderConfig) -> LLMProvider:
    """Factory function to create LLM provider from config."""
    model_lower = config.model.lower()

    if "mock" in model_lower or config.extra.get("mock", False):
        return MockLLMProvider(config)

    if any(x in model_lower for x in ["gpt", "openai", "azure"]):
        from ragent.core.llm_openai import OpenAILLMProvider
        return OpenAILLMProvider(config)

    if any(x in model_lower for x in ["qwen", "dashscope"]):
        from ragent.core.llm_qwen import QwenLLMProvider
        return QwenLLMProvider(config)

    if "glm" in model_lower:
        from ragent.core.llm_glm import GLMLLMProvider
        return GLMLLMProvider(config)

    if "llama" in model_lower:
        from ragent.core.llm_llama import LlamaLLMProvider
        return LlamaLLMProvider(config)

    raise ValueError(f"Unknown LLM provider for model: {config.model}")