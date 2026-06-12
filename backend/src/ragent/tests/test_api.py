"""Unit tests for API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_endpoint_returns_structure(client: AsyncClient) -> None:
    """Test chat endpoint returns expected structure."""
    response = await client.post(
        "/v1/chat",
        json={"query": "Test question", "stream": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "answer" in data
    assert "citations" in data
    assert "traces" in data


@pytest.mark.asyncio
async def test_ingest_endpoint_returns_structure(client: AsyncClient) -> None:
    """Test ingest endpoint returns expected structure."""
    files = {"file": ("test.txt", b"Test content", "text/plain")}
    response = await client.post("/v1/ingest", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "ingest_id" in data
    assert "status" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_retrieve_endpoint_returns_structure(client: AsyncClient) -> None:
    """Test retrieve endpoint returns expected structure."""
    response = await client.post(
        "/v1/retrieve",
        params={"query": "test", "top_k": 10},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test"
    assert data["chunks"] == []


@pytest.mark.asyncio
async def test_agents_list_endpoint(client: AsyncClient) -> None:
    """Test agents list endpoint."""
    response = await client.get("/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_skills_list_endpoint(client: AsyncClient) -> None:
    """Test skills list endpoint."""
    response = await client.get("/v1/skills")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_skill_endpoint(client: AsyncClient) -> None:
    """Test get specific skill endpoint."""
    response = await client.get("/v1/skills/search_documents")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "search_documents"


@pytest.mark.asyncio
async def test_get_unknown_skill_returns_404(client: AsyncClient) -> None:
    """Test getting unknown skill returns 404."""
    response = await client.get("/v1/skills/unknown_skill")
    assert response.status_code == 404