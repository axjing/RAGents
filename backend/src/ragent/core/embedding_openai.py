"""OpenAI-compatible Embedding Provider implementation."""

from __future__ import annotations

from typing import Any

import httpx

from ragent.core.embedding import EmbeddingProvider
from ragent.core.types import EmbeddingResponse, ProviderConfig


# Model to dimension mapping
OPENAI_EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI-compatible embedding provider."""

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
        self._dimension = OPENAI_EMBEDDING_DIMENSIONS.get(config.model, 1536)

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
        raise NotImplementedError("OpenAI embedding models don't support images directly")

    @property
    def model_name(self) -> str:
        return self.config.model

    @property
    def dimension(self) -> int:
        return self._dimension

    async def close(self) -> None:
        await self._client.aclose()