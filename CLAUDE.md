# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DataChat is a self-hosted text-to-SQL chat interface forked from vanna-ai/vanna 2.0.2. Users ask questions in natural language; the system generates SQL, executes it, and returns results with optional Plotly charts. The LLM (Gemini by default) uses RAG over database schema stored in ChromaDB to produce correct SQL.

## Commands

```bash
# Install (use uv, not pip)
uv venv .venv --python 3.12 && source .venv/bin/activate
uv pip install -e ".[gemini,postgres,chromadb,fastapi]" python-dotenv

# Build frontend
cd frontends/webcomponent && npm install && npm run build && cd ../..

# Run server (trains schema first)
python start.py

# Run server only (existing training data)
python main.py

# Train schema separately
python train.py --fresh            # Clear + reload all
python train.py --postgres-only    # PostgreSQL only
python train.py --bigquery-only    # BigQuery only

# Tests
tox -e py311-unit                  # Unit tests (no external deps)
pytest tests/test_tool_permissions.py -v  # Single test file
pytest tests/ -v -m anthropic      # Tests by marker

# Lint & type check
ruff format src/vanna/ tests/      # Auto-format
ruff check src/vanna/ tests/       # Lint
tox -e mypy                        # Type checking (strict mode)
tox -e ruff                        # Format check via tox
```

## Architecture

**Data flow:** User query (WebSocket/SSE) -> FastAPI -> Agent -> LLM (Gemini) with schema context from ChromaDB -> Tool execution (RunSqlTool -> SqlRunner -> DataFrame) -> UI components streamed back to frontend.

**Key abstractions** (all in `src/vanna/`):

- **Agent** (`core/agent/agent.py`) — Main orchestrator. Has 7 extensibility points: lifecycle_hooks, llm_middlewares, error_recovery_strategy, context_enrichers, llm_context_enhancer, conversation_filters, observability_provider.
- **LlmService** (`core/llm/base.py`) — Abstract LLM interface. Primary implementation: `integrations/google/gemini.py`.
- **SqlRunner** (`capabilities/sql_runner/`) — Abstract SQL executor. Primary: `integrations/postgres/sql_runner.py`.
- **AgentMemory** (`capabilities/agent_memory/`) — Vector store for schema/docs RAG. Primary: `integrations/chromadb/agent_memory.py`. Data persisted in `chroma_data/`.
- **Tools** (`tools/`) — RunSqlTool, VisualizeDataTool, AgentMemoryTool. Each has a schema, `execute()` method, and access_groups.
- **Tool Registry** (`core/registry.py`) — Manages tool registration and access control.
- **Components** (`components/`) — UI component definitions streamed to the frontend.
- **Server** (`servers/fastapi/routes.py`) — FastAPI routes with SSE and WebSocket endpoints.

**Frontend** (`frontends/webcomponent/`) — TypeScript + Lit web components, built with Vite. Storybook for component docs.

**Entry points:** `start.py` (train + serve), `main.py` (serve only), `train.py` (train only). Server runs on port 8084 by default.

## Code Conventions

- Python 3.11+, fully async with type hints (mypy strict)
- Formatter/linter: ruff (line length 88)
- Avoid circular imports: use `TYPE_CHECKING` guard
- Commit messages: conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`)
- Tests use pytest markers for external services (`@pytest.mark.anthropic`, `@pytest.mark.postgres`, etc.)
- Unit tests must not require external dependencies

## Configuration

Environment variables in `.env` (see `.env.example`). Key vars: `GOOGLE_API_KEY`, `GEMINI_MODEL`, `POSTGRES_HOST/PORT/DATABASE/USER/PASSWORD`, `BIGQUERY_PROJECT_ID`, `HOST`, `PORT`.
