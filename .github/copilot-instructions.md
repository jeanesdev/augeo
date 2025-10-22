# augeo-platform Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-19

## Active Technologies
- Python 3.11+ (Backend), TypeScript (Frontend) + FastAPI, SQLAlchemy, Pydantic, React, Zustand (002-npo-creation)

## Project Structure
```
src/
tests/
```

## Commands

### Backend (Python)
**CRITICAL**: Always use Poetry for Python commands. Never use pip, venv, or virtualenv directly.

- Run tests: `cd backend && poetry run pytest`
- Run linter: `cd backend && poetry run ruff check .`
- Run formatter: `cd backend && poetry run black .`
- Install dependencies: `cd backend && poetry install`
- Add package: `cd backend && poetry add <package>`
- Run any Python command: `cd backend && poetry run <command>`

### Frontend
- Install: `pnpm install`
- Dev server: `pnpm dev`
- Build: `pnpm build`
- Test: `pnpm test`

## Development Environment

### Python Environment
- **Package Manager**: Poetry (ALWAYS use `poetry run` for all Python commands)
- **Virtual Environment**: Managed by Poetry at `~/.cache/pypoetry/virtualenvs/`
- **Never use**: pip install, venv/bin/activate, python -m commands directly
- **Always use**: `poetry run python`, `poetry run pytest`, etc.

## Code Style
Python 3.11+ (Backend), TypeScript (Frontend): Follow standard conventions

## Recent Changes
- 002-npo-creation: Added Python 3.11+ (Backend), TypeScript (Frontend) + FastAPI, SQLAlchemy, Pydantic, React, Zustand

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
