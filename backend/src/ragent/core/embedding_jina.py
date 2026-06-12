"""Jina AI Embedding Provider implementation."""

from __future__ import annotations

from typing import Any

import httpx

from ragent.core.embedding import EmbeddingProvider
from ragent.core.types import EmbeddingResponse, ProviderConfig


JINA_EMBEDDING_DIMENSIONS = {
    "jina-embeddings-v2-base-en": 768,
    "jina-embeddings-v2-small-en": 512,
    "jina-embeddings-v3": 1024,
    "jina-clip-v1": 768,
    "jina-clip-v2": 1024,
}


class JinaEmbeddingProvider(EmbeddingProvider):
    """Jina AI embedding provider."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client = httpx.AsyncClient(
            base_url=config.base_url or "https://api.jina.ai/v1",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=config.timeout,
        )
        self._dimension = JINA_EMBEDDING_DIMENSIONS.get(config.model, 1024)
        self._is_multimodal = "clip" in config.model.lower()

    async def embed_texts(self, texts: list[str], **kwargs: Any) -> EmbeddingResponse:
        request = {
            "model": self.config.model,
            "input": texts,
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

        request = {
            "model": self.config.model,
            "input": [{"image": img} for img in images],
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