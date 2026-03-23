# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Invoice Generator is a Flask (Python) web application for creating and managing invoices. It uses SQLite for storage, WeasyPrint for PDF generation, and Jinja2 templates for the UI.

### System dependencies

WeasyPrint requires native C libraries (pango, cairo, gdk-pixbuf, etc.). These are installed via apt and must be present before pip install succeeds. See `Dockerfile.dev` for the canonical list.

### Running the dev server

```bash
source venv/bin/activate
export FLASK_APP=app_factory.py
export FLASK_ENV=development
mkdir -p instance/db uploads
flask run --host=0.0.0.0 --port=8080
```

The app is then available at `http://localhost:8080`. Routes include `/login`, `/register`, `/dashboard`, `/create_invoice`, `/businesses`, `/clients`, etc.

### Running tests

```bash
source venv/bin/activate
mkdir -p instance/db
python -m pytest tests/ -v --ignore=tests/test_invoice_draft_api.py
```

**Known issues (pre-existing):**
- `tests/test_invoice_draft_api.py` has a broken import (`from app import app` — `app.py` does not export an `app` object; the app is created in `app_factory.py`). Skip this file with `--ignore`.
- 6 tests in `test_items.py` fail due to raw SQL strings passed to SQLAlchemy session without `text()` wrapper. These are pre-existing code bugs, not environment issues.

### Linting

```bash
source venv/bin/activate
flake8 --max-line-length=200 .
black --check .
```

Pre-existing lint warnings exist (unused imports, formatting). These are in the existing codebase.

### Key gotchas

- The module-level `app = create_app()` in `app_factory.py` runs on import and tries to create the SQLite DB file. Ensure `instance/db/` directory exists before importing or running.
- The `docker-compose.dev.yml` sets `FLASK_APP=app.py` but the correct entry point is `app_factory.py`. When running locally (outside Docker), always set `FLASK_APP=app_factory.py`.
- The app uses `APPLICATION_ROOT = '/invoice'` but when running locally without a reverse proxy, routes work without the `/invoice` prefix.
- Google Maps API key is optional; the app works fully without it (address autocomplete is just disabled).
