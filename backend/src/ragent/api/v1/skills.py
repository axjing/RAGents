"""Skill management API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

router = APIRouter()


class SkillSpec(BaseModel):
    name: str
    description: str
    inputs: dict[str, Any] = {}
    outputs: dict[str, Any] = {}
    tools: list[str] = []
    prompt_template: str
    examples: list[dict[str, Any]] = []


class SkillResponse(BaseModel):
    name: str
    description: str
    enabled: bool


@router.get("/skills", response_model=list[SkillResponse])
async def list_skills() -> list[SkillResponse]:
    """List registered skills."""
    # TODO: Load from skill registry
    return [
        SkillResponse(
            name="search_documents",
            description="Search documents in the knowledge base",
            enabled=True,
        ),
        SkillResponse(
            name="search_web",
            description="Search the web for current information",
            enabled=False,
        ),
    ]


@router.get("/skills/{skill_name}", response_model=SkillSpec)
async def get_skill(skill_name: str) -> SkillSpec:
    """Get skill specification."""
    # TODO: Load from skill registry
    if skill_name == "search_documents":
        return SkillSpec(
            name="search_documents",
            description="Search documents in the knowledge base",
            inputs={"query": "string", "top_k": "int"},
            outputs={"chunks": "list[Chunk]"},
            tools=["vector_search", "bm25_search"],
            prompt_template="Search for relevant documents...",
            examples=[],
        )
    raise HTTPException(status_code=404, detail="Skill not found")


@router.post("/skills", response_model=SkillResponse)
async def register_skill(skill: SkillSpec) -> SkillResponse:
    """Register a new skill."""
    # TODO: Save to skill registry
    return SkillResponse(
        name=skill.name,
        description=skill.description,
        enabled=True,
    )


@router.delete("/skills/{skill_name}")
async def unregister_skill(skill_name: str) -> dict[str, str]:
    """Unregister a skill."""
    # TODO: Remove from skill registry
    return {"message": f"Skill {skill_name} unregistered"}