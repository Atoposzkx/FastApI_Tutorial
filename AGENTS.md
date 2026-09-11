# Repository Guidelines

## Project Structure & Module Organization

Application code lives under `src/fast_api/`. `app.py` defines the FastAPI application and HTTP routes; `main.py` is the Uvicorn entry point. Database models, the async SQLAlchemy engine, and session dependency live in `db.py`. Keep Pydantic request and response models in `schemas.py`, ImageKit setup in `images.py`, and user-related code in `user.py`. The repository currently has no committed test or static-asset directories. Add tests under `tests/`, mirroring source modules when practical (for example, `tests/test_app.py`).

## Build, Test, and Development Commands

- `uv sync`: create or update `.venv` from `pyproject.toml` and `uv.lock`.
- `uv run python -m fast_api.main`: run the application through its Python entry point.
- `uv run uvicorn fast_api.app:app --reload`: start the development server with automatic reload.
- `uv run python -m py_compile src/fast_api/*.py`: perform a quick syntax check.
- `uv run pytest`: run tests after pytest is added to the development dependencies.

API documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

## Coding Style & Naming Conventions

Use Python 3.12 syntax, four-space indentation, and PEP 8 spacing. Use `snake_case` for modules, variables, and functions; use `PascalCase` for SQLAlchemy models and Pydantic schemas. Add type annotations to route parameters, return models, and reusable helpers. Keep route functions focused: validation belongs in schemas, persistence in database helpers/models, and external media configuration in `images.py`. No formatter or linter is configured yet; avoid unrelated formatting changes.

## Testing Guidelines

No automated test framework or coverage threshold is currently configured. New endpoint behavior should include pytest tests named `test_<behavior>`. Use FastAPI's test client or `httpx.AsyncClient`, and isolate database tests with a temporary SQLite database. Mock ImageKit calls so tests do not upload real files or require credentials.

## Commit & Pull Request Guidelines

History uses short feature-focused messages, including Conventional Commit prefixes. Prefer messages such as `feat: add post deletion endpoint`, `fix: validate uploaded media type`, or `docs: explain database session lifecycle`. Keep each commit scoped to one logical change. Pull requests should describe behavior changes, list verification commands, link relevant issues, and include sample requests/responses for API changes.

## Security & Configuration

Keep `.env`, ImageKit private keys, virtual environments, and local SQLite files out of commits. Document required variable names, such as `IMAGEKIT_PRIVATE_KEY`, without including values. Never use production credentials in tests.
