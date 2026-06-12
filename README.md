# Ragent — Agentic RAG System

> A multi-modal, hierarchical intelligent retrieval QA system built from scratch without LangChain or LlamaIndex.

## Architecture Overview

Ragent implements an **agentic RAG** approach where:
- Each document collection is managed by an independent **sub-agent**
- A **harness (main controller)** handles task decomposition, sub-agent scheduling, result synthesis, and reflection
- Uses **ReAct / Loops / Reflection / Tool-Calling** paradigms for complex reasoning
- **skill.md** mechanism enables dynamic capability registration via declarative files

## Tech Stack

| Layer | Technology |
|-------|------------|
| LLM | Qwen3-VL, GLM, Llama (OpenAI/Azure/DashScope compatible) |
| Embedding | Qwen2.5-VL, JinaCLIP, bge-m3 (multimodal) |
| Retrieval | BM25 + Vector (Hybrid) + Reranker |
| Vector DB | PgVector + Milvus (dual backend) |
| Database | PostgreSQL |
| Backend | Python 3.12+, FastAPI, Pydantic, asyncio |
| Frontend | TypeScript, React, Vite |
| Message Bus | asyncio.Queue (Redis Stream ready) |
| Deployment | Docker Compose / Kubernetes |

## Project Structure

```
RAGents/
├── PLAN.md                      # Implementation plan
├── AGENTS.md                    # Development rules
├── docker-compose.yml           # PostgreSQL + PgVector + Milvus + MinIO
├── backend/
│   ├── pyproject.toml           # Python dependencies (uv/poetry)
│   ├── src/ragent/
│   │   ├── config/              # Settings, env vars
│   │   ├── core/                # LLMProvider, EmbeddingProvider abstractions
│   │   ├── db/                  # SQLAlchemy models + Alembic migrations
│   │   ├── ingest/              # Extractor, chunker, indexer
│   │   ├── retrieval/           # Hybrid retriever, reranker, citation index
│   │   ├── agents/              # Agent base, ReActAgent, SubAgent
│   │   ├── harness/             # Planner, Router, Synthesizer, Reflection
│   │   ├── tools/               # Tool base + built-in tools
│   │   ├── skills/              # SkillSpec, SkillCompiler, SkillRegistry
│   │   ├── memory/              # Short/long term memory
│   │   ├── api/                 # FastAPI routers
│   │   └── server.py            # FastAPI app entry
│   └── tests/                   # pytest tests
├── frontend/
│   ├── package.json             # Node dependencies
│   ├── src/
│   │   ├── app/                 # Routes & pages
│   │   ├── components/          # Chat, upload, agent visualization
│   │   ├── store/               # nanostores (per AGENTS.md)
│   │   └── lib/                 # API client + utils
└── skills/                      # Runtime hot-loadable skill.md files
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local development)
- Node.js 20+ (for frontend development)

### Using Docker Compose (Recommended)

```bash
# Start all services
docker compose up -d

# Check service health
curl http://localhost:8000/v1/ping
# {"ok": true}

# Access frontend
open http://localhost:3000
```

### Local Development

**Backend:**
```bash
cd backend
# Install uv (fast Python package manager)
pip install uv

# Install dependencies
uv sync --all-extras

# Copy environment template
cp ../.env.example .env

# Run database migrations
uv run alembic upgrade head

# Start server
uv run uvicorn ragent.server:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### CLI Demo

```bash
cd backend
uv run python -m ragent demo-chat "What is Ragent?"
```

## Milestones

| Milestone | Description | Status |
|-----------|-------------|--------|
| **M0** | Scaffold & Infrastructure | ✅ Done |
| **M1** | Document Ingestion & Multimodal Indexing | 🔄 Planned |
| **M2** | Single Agent & ReAct Loop | 🔄 Planned |
| **M3** | Harness: Multi-Agent Coordination | 🔄 Planned |
| **M4** | Skill Mechanism (skill.md) | 🔄 Planned |
| **M5** | Multimodal Input/Retrieval | 🔄 Planned |
| **M6** | Frontend & UX | 🔄 Planned |
| **M7** | Production Hardening | 🔄 Planned |

See [PLAN.md](PLAN.md) for detailed milestones and acceptance criteria.

## Development

### Code Quality

```bash
# Backend
cd backend
uv run ruff check .
uv run ruff format .
uv run mypy src/ragent
uv run pytest -v

# Frontend
cd frontend
npm run lint
npm run type-check
npm run build
```

### Testing

```bash
# Run all tests
cd backend
uv run pytest -v --cov=src/ragent

# Run specific test
uv run pytest src/ragent/tests/test_e2e_chat.py -v
```

### Database Migrations

```bash
cd backend
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head
```

## Key Principles

1. **No LangChain/LlamaIndex** — All agent/harness logic is custom
2. **Testability** — Every module has MockProvider for offline testing
3. **Observability** — Every agent step produces `AgentTrace` with citations
4. **Extensibility** — New LLM = implement `LLMProvider`; New doc type = add `Extractor`; New capability = write `skill.md`
5. **Security** — No raw file paths exposed; HTTP calls allowlisted; Prompt injection detection

## License

MIT License — see [LICENSE](LICENSE) for details.