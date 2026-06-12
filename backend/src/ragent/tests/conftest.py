"""Pytest configuration and fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from ragent.config.settings import (
    Settings,
    DatabaseSettings,
    LLMSettings,
    EmbeddingSettings,
)
from ragent.db.models import Base
from ragent.db.session import get_session
from ragent.server import create_app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test settings with in-memory database."""
    return Settings(
        environment="test",
        debug=True,
        database=DatabaseSettings(
            host="localhost",
            port=5432,
            user="ragent",
            password="ragent",
            name="ragent_test",
        ),
        llm=LLMSettings(provider="mock", model="mock-gpt-4"),
        embedding=EmbeddingSettings(provider="mock", model="mock-embedding"),
    )


@pytest.fixture(scope="function")
async def mock_db_session():
    """Create a mock database session for tests that don't need real DB."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture(scope="function")
async def app(test_settings: Settings, mock_db_session):
    """Create test FastAPI application with mocked database."""
    app = create_app()

    # Override database dependency with mock
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield mock_db_session

    app.dependency_overrides[get_session] = override_get_session
    return app


@pytest.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_document() -> dict[str, Any]:
    """Sample document data for testing."""
    return {
        "id": str(uuid4()),
        "title": "Test Document",
        "doc_type": "text",
        "text": "This is a test document about Ragent, an agentic RAG system.",
        "metadata": {"author": "Test Author"},
    }


@pytest.fixture
def sample_chunk() -> dict[str, Any]:
    """Sample chunk data for testing."""
    return {
        "id": str(uuid4()),
        "document_id": str(uuid4()),
        "doc_type": "text",
        "text": "Ragent is an agentic RAG system for intelligent retrieval.",
        "page": 1,
        "span_start": 0,
        "span_end": 50,
        "embedding": [0.1] * 768,
        "metadata": {},
    }