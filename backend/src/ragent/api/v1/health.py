"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ragent.db.session import get_session

router = APIRouter()


@router.get("/ping")
async def ping() -> dict[str, bool]:
    """Simple health check endpoint."""
    return {"ok": True}


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Detailed health check with database connectivity."""
    db_ok = False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Readiness check for Kubernetes."""
    db_ok = False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    if not db_ok:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not ready")

    return {"ready": True}