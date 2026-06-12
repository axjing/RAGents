"""Embedding Provider abstraction for Ragent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ragent.core.types import EmbeddingResponse, ProviderConfig


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def embed_texts(self, texts: list[str], **kwargs: Any) -> EmbeddingResponse:
        """Generate embeddings for a list of texts."""
        ...

    @abstractmethod
    async def embed_images(self, images: list[str], **kwargs: Any) -> EmbeddingResponse:
        """Generate embeddings for a list of images (base64 or URLs)."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        ...

    def supports_multimodal(self) -> bool:
        """Check if provider supports multimodal embeddings."""
        return False


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._dimension = config.extra.get("dimension", 768)

    async def embed_texts(self, texts: list[str], **kwargs: Any) -> EmbeddingResponse:
        import random
        embeddings = [[random.random() for _ in range(self._dimension)] for _ in texts]
        return EmbeddingResponse(
            embeddings=embeddings,
            usage={"prompt_tokens": sum(len(t) for t in texts), "total_tokens": sum(len(t) for t in texts)},
            model=self.config.model,
        )

    async def embed_images(self, images: list[str], **kwargs: Any) -> EmbeddingResponse:
        import random
        embeddings = [[random.random() for _ in range(self._dimension)] for _ in images]
        return EmbeddingResponse(
            embeddings=embeddings,
            usage={"prompt_tokens": len(images) * 100, "total_tokens": len(images) * 100},
            model=self.config.model,
        )

    @property
    def model_name(self) -> str:
        return self.config.model

    @property
    def dimension(self) -> int:
        return self._dimension

    def supports_multimodal(self) -> bool:
        return True


def create_embedding_provider(config: ProviderConfig) -> EmbeddingProvider:
    """Factory function to create embedding provider from config."""
    model_lower = config.model.lower()

    if "mock" in model_lower or config.extra.get("mock", False):
        return MockEmbeddingProvider(config)

    if any(x in model_lower for x in ["openai", "text-embedding"]):
        from ragent.core.embedding_openai import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider(config)

    if any(x in model_lower for x in ["qwen", "dashscope"]):
        from ragent.core.embedding_qwen import QwenEmbeddingProvider
        return QwenEmbeddingProvider(config)

    if "jina" in model_lower:
        from ragent.core.embedding_jina import JinaEmbeddingProvider
        return JinaEmbeddingProvider(config)

    if "bge" in model_lower:
        from ragent.core.embedding_bge import BGEEmbeddingProvider
        return BGEEmbeddingProvider(config)

    raise ValueError(f"Unknown embedding provider for model: {config.model}")