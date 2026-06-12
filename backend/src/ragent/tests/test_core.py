"""Unit tests for core abstractions."""

from __future__ import annotations

import pytest
from ragent.core.types import (
    Chunk,
    DocType,
    ToolCall,
    AgentTrace,
    ChatTurn,
    LLMMessage,
    LLMResponse,
    EmbeddingResponse,
    ProviderConfig,
)
from ragent.core.llm import MockLLMProvider, create_llm_provider
from ragent.core.embedding import MockEmbeddingProvider, create_embedding_provider
from uuid import uuid4
from datetime import datetime


class TestTypes:
    """Test core type definitions."""

    def test_chunk_creation(self) -> None:
        chunk = Chunk(
            id=uuid4(),
            document_id=uuid4(),
            doc_type=DocType.TEXT,
            text="Test chunk",
            page=1,
        )
        assert chunk.doc_type == DocType.TEXT
        assert chunk.text == "Test chunk"
        assert chunk.page == 1

    def test_tool_call_creation(self) -> None:
        tool_call = ToolCall(
            tool_name="search_documents",
            arguments={"query": "test"},
            observation="Found 3 results",
            citations=[uuid4()],
        )
        assert tool_call.tool_name == "search_documents"
        assert tool_call.arguments["query"] == "test"
        assert len(tool_call.citations) == 1

    def test_agent_trace_creation(self) -> None:
        trace = AgentTrace(
            step=1,
            thought="I need to search for information",
            tool_call=ToolCall(
                tool_name="search_documents",
                arguments={"query": "test"},
            ),
        )
        assert trace.step == 1
        assert trace.thought == "I need to search for information"
        assert trace.tool_call is not None

    def test_chat_turn_creation(self) -> None:
        turn = ChatTurn(
            user_query="What is Ragent?",
            answer="Ragent is an agentic RAG system.",
        )
        assert turn.user_query == "What is Ragent?"
        assert turn.answer == "Ragent is an agentic RAG system."

    def test_llm_message_creation(self) -> None:
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_provider_config(self) -> None:
        config = ProviderConfig(
            model="gpt-4",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
        )
        assert config.model == "gpt-4"
        assert config.api_key == "test-key"


class TestMockLLMProvider:
    """Test mock LLM provider."""

    @pytest.mark.asyncio
    async def test_mock_chat(self) -> None:
        config = ProviderConfig(model="mock-gpt-4", extra={"mock": True})
        provider = MockLLMProvider(config)

        response = await provider.chat([
            {"role": "user", "content": "Hello"}
        ])

        assert response.content == "Mock response"
        assert response.model == "mock-gpt-4"
        assert response.usage is not None

    @pytest.mark.asyncio
    async def test_mock_chat_with_canned_responses(self) -> None:
        config = ProviderConfig(model="mock-gpt-4", extra={"mock": True})
        provider = MockLLMProvider(config)

        canned = LLMResponse(
            content="Canned response",
            model="mock-gpt-4",
            usage={"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        )
        provider.add_response(canned)

        response = await provider.chat([
            {"role": "user", "content": "Hello"}
        ])

        assert response.content == "Canned response"

    @pytest.mark.asyncio
    async def test_mock_chat_stream(self) -> None:
        config = ProviderConfig(model="mock-gpt-4", extra={"mock": True})
        provider = MockLLMProvider(config)

        chunks = []
        async for chunk in provider.chat_stream([
            {"role": "user", "content": "Hello"}
        ]):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert "".join(chunks).strip() == "Mock response"


class TestMockEmbeddingProvider:
    """Test mock embedding provider."""

    @pytest.mark.asyncio
    async def test_mock_embed_texts(self) -> None:
        config = ProviderConfig(model="mock-embedding", extra={"mock": True, "dimension": 768})
        provider = MockEmbeddingProvider(config)

        response = await provider.embed_texts(["text1", "text2"])

        assert len(response.embeddings) == 2
        assert len(response.embeddings[0]) == 768
        assert len(response.embeddings[1]) == 768
        assert response.model == "mock-embedding"

    @pytest.mark.asyncio
    async def test_mock_embed_images(self) -> None:
        config = ProviderConfig(model="mock-embedding", extra={"mock": True, "dimension": 768})
        provider = MockEmbeddingProvider(config)

        response = await provider.embed_images(["image1", "image2"])

        assert len(response.embeddings) == 2
        assert len(response.embeddings[0]) == 768

    def test_mock_properties(self) -> None:
        config = ProviderConfig(model="mock-embedding", extra={"mock": True, "dimension": 512})
        provider = MockEmbeddingProvider(config)

        assert provider.model_name == "mock-embedding"
        assert provider.dimension == 512
        assert provider.supports_multimodal() is True


class TestProviderFactory:
    """Test provider factory functions."""

    def test_create_mock_llm_provider(self) -> None:
        config = ProviderConfig(model="mock-gpt-4", extra={"mock": True})
        provider = create_llm_provider(config)
        assert isinstance(provider, MockLLMProvider)

    def test_create_mock_embedding_provider(self) -> None:
        config = ProviderConfig(model="mock-embedding", extra={"mock": True})
        provider = create_embedding_provider(config)
        assert isinstance(provider, MockEmbeddingProvider)

    def test_create_unknown_llm_provider_raises(self) -> None:
        config = ProviderConfig(model="unknown-model")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider(config)

    def test_create_unknown_embedding_provider_raises(self) -> None:
        config = ProviderConfig(model="unknown-embedding")
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            create_embedding_provider(config)