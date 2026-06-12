"""Agent management API endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

router = APIRouter()


class AgentInfo(BaseModel):
    name: str
    type: str
    description: str
    capabilities: list[str] = []


@router.get("/agents", response_model=list[AgentInfo])
async def list_agents() -> list[AgentInfo]:
    """List available agents."""
    return [
        AgentInfo(
            name="react-agent",
            type="ReActAgent",
            description="Standard ReAct agent for document QA",
            capabilities=["search_documents", "read_chunk", "synthesize"],
        ),
    ]


@router.get("/agents/{agent_name}")
async def get_agent(agent_name: str) -> dict[str, Any]:
    """Get agent details."""
    return {
        "name": agent_name,
        "type": "ReActAgent",
        "description": "Standard ReAct agent for document QA",
        "capabilities": ["search_documents", "read_chunk", "synthesize"],
        "status": "available",
    }


@router.post("/agents/{agent_name}/run")
async def run_agent(agent_name: str, input: dict[str, Any]) -> dict[str, Any]:
    """Run an agent with given input."""
    # TODO: Implement agent execution
    return {
        "agent": agent_name,
        "output": "Agent execution not yet implemented",
        "traces": [],
    }