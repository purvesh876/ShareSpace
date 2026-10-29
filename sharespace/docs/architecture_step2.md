# ShareSpace Architecture & Foundations (Step 2)

## Overview
ShareSpace is a resource-sharing platform designed for colleges, research laboratories, and institutional communities to unlock underused equipment and spaces.

## Core Invariants
1. **Dedicated Backend Gateway**: All authorization, concurrency locking, and audit verification occur in FastAPI. Frontend never dictates roles or permissions.
2. **PostgreSQL Exclusivity**: PostgreSQL is the only supported database. SQLite lacks the range exclusion constraints (`btree_gist`) and concurrency isolation needed for reliable resource bookings.
3. **Private Handover Evidence**: Evidence photos (during check-in and return) are strictly private. The browser cannot directly read or write files without signed, time-limited credentials issued by FastAPI.

## Directory Structure
- `frontend/`: React 19 + TypeScript + Vite + Tailwind CSS + shadcn/ui primitives.
- `backend/`: FastAPI + Pydantic v2 + SQLAlchemy 2.0 (asyncpg) + Alembic.
- `docs/`: Design and architectural documentation.
