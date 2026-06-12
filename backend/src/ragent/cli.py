"""Command-line interface for Ragent."""

from __future__ import annotations

import asyncio
import sys
from typing import Any

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ragent.config.settings import get_settings
from ragent.core.llm import create_llm_provider
from ragent.core.types import LLMMessage, ProviderConfig

app = typer.Typer(name="ragent", help="Ragent CLI")
console = Console()


@app.command()
def demo_chat(
    message: str = typer.Argument(..., help="Message to send to the agent"),
    model: str = typer.Option("mock-gpt-4", "--model", "-m", help="LLM model to use"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Sampling temperature"),
) -> None:
    """Run a demo chat with the agent."""
    asyncio.run(_demo_chat_async(message, model, temperature))


async def _demo_chat_async(message: str, model: str, temperature: float) -> None:
    settings = get_settings()

    # Create LLM provider
    config = ProviderConfig(
        model=model,
        api_key=settings.llm.api_key,
        base_url=settings.llm.base_url,
        temperature=temperature,
        extra={"mock": model.startswith("mock")},
    )

    provider = create_llm_provider(config)

    # Simple demo conversation
    messages = [
        LLMMessage(role="system", content="You are a helpful AI assistant called Ragent."),
        LLMMessage(role="user", content=message),
    ]

    console.print(Panel(f"[bold]User:[/bold] {message}", border_style="blue"))

    try:
        response = await provider.chat(messages, temperature=temperature)
        console.print(Panel(Markdown(response.content or "No response"), border_style="green", title="Ragent"))
    except Exception as e:
        console.print(Panel(f"[red]Error:[/red] {e}", border_style="red"))
        sys.exit(1)
    finally:
        if hasattr(provider, "close"):
            await provider.close()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
) -> None:
    """Start the API server."""
    import uvicorn

    uvicorn.run(
        "ragent.server:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def init_db() -> None:
    """Initialize the database."""
    from ragent.db.session import init_db

    asyncio.run(_init_db_async())
    console.print("[green]Database initialized successfully![/green]")


async def _init_db_async() -> None:
    await init_db()


if __name__ == "__main__":
    app()