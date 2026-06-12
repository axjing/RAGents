"""BGE Embedding Provider implementation (local/inference server)."""

from __future__ import annotations

from typing import Any

import httpx

from ragent.core.embedding import EmbeddingProvider
from ragent.core.types import EmbeddingResponse, ProviderConfig


BGE_EMBEDDING_DIMENSIONS = {
    "bge-m3": 1024,
    "bge-large-en-v1.5": 1024,
    "bge-base-en-v1.5": 768,
    "bge-small-en-v1.5": 384,
    "bge-large-zh-v1.5": 1024,
    "bge-base-zh-v1.5": 768,
    "bge-small-zh-v1.5": 384,
}


class BGEEmbeddingProvider(EmbeddingProvider):
    """BGE embedding provider (compatible with TEI, vLLM, or custom inference servers)."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client = httpx.AsyncClient(
            base_url=config.base_url or "http://localhost:8080",
            headers={"Content-Type": "application/json"},
            timeout=config.timeout,
        )
        self._dimension = BGE_EMBEDDING_DIMENSIONS.get(config.model, 1024)

    async def embed_texts(self, texts: list[str], **kwargs: Any) -> EmbeddingResponse:
        # TEI-compatible format
        request = {
            "inputs": texts,
            "truncate": True,
        }
        request.update(kwargs)

        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.post("/embed", json=request)
                response.raise_for_status()
                data = response.json()

                # TEI returns list of embeddings directly
                embeddings = data if isinstance(data, list) else data.get("embeddings", [])
                return EmbeddingResponse(
                    embeddings=embeddings,
                    usage={"total_tokens": sum(len(t.split()) for t in texts)},
                    model=self.config.model,
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
        raise NotImplementedError("BGE models do not support image embeddings")

    @property
    def model_name(self) -> str:
        return self.config.model

    @property
    def dimension(self) -> int:
        return self._dimension

    async def close(self) -> None:
        await self._client.aclose()