"""Qwen/DashScope Embedding Provider implementation."""

from __future__ import annotations

from typing import Any

import httpx

from ragent.core.embedding import EmbeddingProvider
from ragent.core.types import EmbeddingResponse, ProviderConfig


QWEN_EMBEDDING_DIMENSIONS = {
    "text-embedding-v1": 1536,
    "text-embedding-v2": 1536,
    "text-embedding-v3": 1024,
    "text-embedding-v4": 1024,
    "multimodal-embedding-v1": 1024,
}


class QwenEmbeddingProvider(EmbeddingProvider):
    """Qwen/DashScope embedding provider."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client = httpx.AsyncClient(
            base_url=config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=config.timeout,
        )
        self._dimension = QWEN_EMBEDDING_DIMENSIONS.get(config.model, 1024)
        self._is_multimodal = "multimodal" in config.model.lower()

    async def embed_texts(self, texts: list[str], **kwargs: Any) -> EmbeddingResponse:
        request = {
            "model": self.config.model,
            "input": texts,
            "encoding_format": "float",
        }
        request.update(kwargs)

        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.post("/embeddings", json=request)
                response.raise_for_status()
                data = response.json()

                embeddings = [item["embedding"] for item in data["data"]]
                return EmbeddingResponse(
                    embeddings=embeddings,
                    usage=data.get("usage"),
                    model=data.get("model"),
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

    async def embed_images(self, images: list[str], **kwargs: Any) -> EmbeddingResponse:
        if not self._is_multimodal:
            raise NotImplementedError(f"Model {self.config.model} does not support image embeddings")

        # For multimodal models, images are typically passed as base64 in the input
        # This is a simplified implementation - actual API may differ
        request = {
            "model": self.config.model,
            "input": [{"image": img} for img in images],
            "encoding_format": "float",
        }
        request.update(kwargs)

        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.post("/embeddings", json=request)
                response.raise_for_status()
                data = response.json()

                embeddings = [item["embedding"] for item in data["data"]]
                return EmbeddingResponse(
                    embeddings=embeddings,
                    usage=data.get("usage"),
                    model=data.get("model"),
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

    @property
    def model_name(self) -> str:
        return self.config.model

    @property
    def dimension(self) -> int:
        return self._dimension

    def supports_multimodal(self) -> bool:
        return self._is_multimodal

    async def close(self) -> None:
        await self._client.aclose()