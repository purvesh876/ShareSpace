# ShareSpace Backend

FastAPI application service for the ShareSpace campus resource sharing platform.

## Features
- Dedicated application service for complex multi-stage booking state machines.
- PostgreSQL exclusivity with range exclusion concurrency locking.
- Environment-based configuration with Pydantic Settings.
- Structured application logging with automatic sensitive keyword scrubbing.
- Alembic database migration management.

## Getting Started
```bash
# Create virtual environment
uv venv --python 3.13 .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Start development server
uvicorn app.main:app --reload --port 8000
```
