"""End-to-end tests for chat functionality."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_ping_endpoint(client: AsyncClient) -> None:
    """Test that the ping endpoint returns ok."""
    response = await client.get("/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Test that the health endpoint returns status."""
    response = await client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_chat_endpoint_structure(client: AsyncClient) -> None:
    """Test that chat endpoint returns expected structure."""
    response = await client.post(
        "/v1/chat",
        json={
            "query": "What is Ragent?",
            "stream": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "answer" in data
    assert "citations" in data
    assert "traces" in data
    assert isinstance(data["citations"], list)
    assert isinstance(data["traces"], list)


@pytest.mark.asyncio
async def test_ingest_document_endpoint(client: AsyncClient) -> None:
    """Test document ingestion endpoint."""
    # Create a simple test file
    files = {"file": ("test.txt", b"This is a test document about Ragent.", "text/plain")}
    response = await client.post("/v1/ingest", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "ingest_id" in data
    assert "status" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_retrieve_endpoint(client: AsyncClient) -> None:
    """Test document retrieval endpoint."""
    response = await client.post(
        "/v1/retrieve",
        params={
            "query": "Ragent",
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "chunks" in data
    assert "total" in data
    assert isinstance(data["chunks"], list)


@pytest.mark.asyncio
async def test_agents_list_endpoint(client: AsyncClient) -> None:
    """Test agents list endpoint."""
    response = await client.get("/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    agent = data[0]
    assert "name" in agent
    assert "type" in agent
    assert "description" in agent
    assert "capabilities" in agent


@pytest.mark.asyncio
async def test_skills_list_endpoint(client: AsyncClient) -> None:
    """Test skills list endpoint."""
    response = await client.get("/v1/skills")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    skill = data[0]
    assert "name" in skill
    assert "description" in skill
    assert "enabled" in skill


# Integration test that would run with actual ingestion and retrieval
# This is a placeholder for when the full pipeline is implemented
@pytest.mark.skip(reason="Requires full ingestion pipeline implementation")
@pytest.mark.asyncio
async def test_full_ingest_chat_flow(client: AsyncClient, sample_document: dict) -> None:
    """
    Test the full flow: ingest document -> chat -> verify citation.
    This test will be enabled when M1 and M2 are implemented.
    """
    # 1. Ingest a document
    files = {"file": ("demo.md", b"# Ragent\n\nRagent is an agentic RAG system.", "text/markdown")}
    ingest_response = await client.post("/v1/ingest", files=files)
    assert ingest_response.status_code == 200
    ingest_data = ingest_response.json()
    ingest_id = ingest_data["ingest_id"]

    # 2. Wait for ingestion to complete (poll status)
    # This would be implemented with a proper status endpoint
    # For now, we assume it's fast with mock providers

    # 3. Ask a question about the document
    chat_response = await client.post(
        "/v1/chat",
        json={
            "query": "What is Ragent?",
            "stream": False,
        },
    )
    assert chat_response.status_code == 200
    chat_data = chat_response.json()

    # 4. Verify answer contains citation
    assert chat_data["answer"] is not None
    assert len(chat_data["answer"]) > 0
    # The answer should contain citation markers like [1]
    # assert "[" in chat_data["answer"] and "]" in chat_data["answer"]

    # 5. Verify citations are present
    assert isinstance(chat_data["citations"], list)
    # When fully implemented, we'd assert len(chat_data["citations"]) > 0