# Repository Guidelines

## Project Structure & Module Organization

Application code lives in `src/fast_api/`. `app.py` owns the FastAPI application, authentication routers, media upload, feed, and delete endpoints. `db.py` contains the `User` and `Post` SQLAlchemy models, async SQLite engine, and session dependencies. Keep JWT and FastAPI Users configuration in `user.py`, Pydantic schemas in `schemas.py`, ImageKit setup in `images.py`, and Uvicorn startup in `main.py`.

`frontend.py` is the Streamlit client. It calls the API at `http://localhost:8000` and stores the JWT in Streamlit session state. Tests live in `tests/`; `tests/test_auth_posts.py` uses an in-memory SQLite database and mocks ImageKit uploads.

## Development and Verification Commands

- `uv sync`: install the locked dependencies into `.venv`.
- `uv run python -m fast_api.main`: run the backend with reload on port 8000.
- `uv run streamlit run frontend.py`: run the frontend on port 8501.
- `uv run python -m unittest discover -s tests -v`: run the test suite.
- `uv run python -m py_compile src/fast_api/*.py frontend.py`: check syntax.

Backend API documentation is available at `http://localhost:8000/docs`.

## Coding Style & Architecture

Use Python 3.12 syntax, four-space indentation, PEP 8 spacing, and type annotations. Use `snake_case` for functions and variables and `PascalCase` for ORM and Pydantic classes. Keep route handlers focused and preserve the dependency chain `get_async_session` → `get_user_db` → `get_user_manager`.

Protected endpoints must use `Depends(current_active_user)`. Derive post ownership from `current_user.id`; never trust a client-supplied user ID. Keep authorization checks in the backend even when the frontend hides controls.

## Testing Guidelines

Add `unittest` tests named `test_<behavior>` for endpoint changes. Use an isolated database and mock external ImageKit requests. Cover anonymous access, authenticated success, ownership rules, and relevant errors. Tests must not modify `.test.db` or upload real files.

## Commit & Pull Request Guidelines

Prefer short, feature-focused Conventional Commit messages, such as `feat: add authenticated media upload` or `fix: enforce post ownership`. Keep commits scoped to one logical change. Pull requests should explain behavior changes, list verification commands, and include sample requests or screenshots when UI behavior changes.

## Security & Configuration

Keep `.env`, `.test.db`, credentials, and virtual environments out of Git. Required configuration includes `AUTH_SECRET` and `IMAGEKIT_PRIVATE_KEY`; `IMAGEKIT_URL_ENDPOINT` is optional. Never log passwords, JWTs, reset tokens, verification tokens, or private keys. `create_all()` does not migrate existing tables; use migrations or recreate only disposable local databases after model changes.
