# ShareSpace — Resource-Sharing Platform for Campus Communities

> **Mission**: Unlock Underused Equipment and Spaces for colleges, research laboratories, and institutional communities.

---

## 1. Project Overview

ShareSpace is a multi-tenant resource-sharing platform engineered to make specialized institutional assets (confocal microscopes, 3D printers, laser cutters, seminar halls, AV equipment) easily discoverable and fairly allocated.

The platform is designed with production-grade engineering principles:
- **Strict Booking Integrity**: Eliminates double-booking at the storage engine level.
- **Mandatory Handover Verification**: Requires written condition checklists and photographic evidence during check-in and return.
- **Transparent Fair-Use**: Enforces anti-monopolization quotas and cooldown periods.
- **Human-in-the-Loop Reviews**: All incident reports, damage assessments, and penalty decisions require authorized human manager review.

---

## 2. Approved Technology Stack

| Layer | Technology | Key Responsibility |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons | Responsive, accessible client UI and state management |
| **Routing** | React Router v7 | Client-side routing with layout and guard structure |
| **Backend** | Python 3.13, FastAPI, Pydantic v2 | Dedicated gateway for complex business workflows and RBAC |
| **ORM & Migrations** | SQLAlchemy 2.0 (asyncpg), Alembic | Type-safe queries, unit-of-work transactions, and schema versioning |
| **Database** | PostgreSQL 16+ | ACID transactions, `btree_gist` range exclusion constraints |
| **Auth & Storage** | Supabase Auth + Supabase Storage | Identity management and private, signed-URL evidence storage (Step 6+) |
| **Testing** | Pytest, pytest-asyncio, Oxlint | Automated unit, integration, and concurrency verification |

---

## 3. Repository Structure

```text
sharespace/
├── frontend/                     # React + Vite + TypeScript Application
│   ├── src/
│   │   ├── api/                  # Typed API client and response interfaces
│   │   ├── components/           # Reusable UI components & layouts
│   │   ├── lib/                  # Utilities (e.g. cn class merge)
│   │   ├── routes/               # Page routes (Home.tsx placeholder)
│   │   ├── App.tsx               # Root router provider
│   │   ├── main.tsx              # Application entry point
│   │   └── index.css             # Tailwind CSS v4 design tokens
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/                      # Python + FastAPI Dedicated Service
│   ├── app/
│   │   ├── api/v1/               # API version 1 routing and endpoints
│   │   ├── core/                 # Config (Pydantic Settings), logging, exceptions
│   │   ├── db/                   # Async PostgreSQL session and Declarative Base
│   │   ├── models/               # SQLAlchemy ORM models (Step 5+)
│   │   ├── schemas/              # Pydantic v2 request/response schemas
│   │   ├── services/             # Pure business logic and domain services
│   │   └── main.py               # FastAPI application lifecycle and CORS setup
│   ├── migrations/               # Alembic database migration scripts
│   ├── tests/                    # Pytest test suite (health, readiness, workflows)
│   ├── alembic.ini               # Alembic configuration
│   └── pyproject.toml            # Python dependencies (managed via uv)
│
├── docs/                         # Architecture Decision Records (ADRs) and specifications
├── .env.example                  # Root environment configuration template
├── .gitignore                    # Comprehensive secrets and build artifact exclusions
└── README.md                     # Project documentation (this file)
```

---

## 4. Prerequisites (macOS)

Ensure the following tools are installed on your system:
- **macOS** with Homebrew (`brew`)
- **Python 3.13**: `brew install python@3.13`
- **uv** (ultra-fast Python package installer): `brew install uv`
- **Node.js 20+** and **npm**: `brew install node`
- **Git**: `brew install git`
- **PostgreSQL 16+** (Local or Managed):
  - Local via Homebrew: `brew install postgresql@16 && brew services start postgresql@16`
  - OR a free cloud instance via Supabase.

---

## 5. Getting Started & Setup Commands

### Step A: Clone & Environment Configuration

1. Copy the environment configuration template:
   ```bash
   cp .env.example .env
   ```
2. Review the settings inside `.env`:
   - `DATABASE_URL`: Set your PostgreSQL connection string when ready.
   - `VITE_API_BASE_URL`: Defaults to `http://localhost:8000/api/v1`.

### Step B: Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a Python 3.13 virtual environment using `uv`:
   ```bash
   uv venv --python 3.13 .venv
   source .venv/bin/activate
   ```
3. Install dependencies in editable mode:
   ```bash
   uv pip install -e ".[dev]"
   ```
4. Run the automated backend tests:
   ```bash
   pytest -v
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The backend API will be available at:
   - Interactive Swagger API Docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
   - Alternative ReDoc: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

### Step C: Frontend Setup (React + Vite)

1. Open a new terminal tab and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the linter and production build to verify:
   ```bash
   npm run lint
   npm run build
   ```
4. Start the frontend development server:
   ```bash
   npm run dev
   ```
   The frontend application will be available at [http://localhost:5173](http://localhost:5173).

---

## 6. Available Health & Diagnostics Endpoints

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API welcome payload and documentation links | `200 OK` |
| `GET` | `/api/v1/health` | Operational health check (app name, version, environment, timestamp) | `200 OK` |
| `GET` | `/api/v1/ready` | Database readiness check. Validates active connection to PostgreSQL. | `200 OK` (connected)<br>`503 Service Unavailable` (unconfigured/unreachable) |

> **Honest Readiness Guarantee**: If `DATABASE_URL` is not set or the PostgreSQL database is unreachable, `/api/v1/ready` returns `503 Service Unavailable` with `database: "not configured"` or `database: "unreachable"`. It will never falsely claim readiness.

---

## 7. How to Run Automated Tests

### Backend Test Suite
```bash
cd backend
source .venv/bin/activate
pytest -v
```

### Frontend Linting & Build Verification
```bash
cd frontend
npm run lint    # Runs Oxlint across source files
npm run build   # Type-checks (tsc) and bundles with Vite
```

---

## 8. Implemented Features & Architecture

ShareSpace MVP is fully implemented and verified end-to-end:
- **Authentication & Multi-Tenant Security**: Real Supabase Auth (ES256 JWKS asymmetric signature verification), server-side institutional user provisioning, organization membership and role authorization (`researcher`, `lab_manager`, `admin`, `auditor`).
- **PostgreSQL Database & RLS**: 8 core tables with strict foreign keys, indexes, and PostgreSQL Row-Level Security enforced via least-privilege role `sharespace_app` with `SET LOCAL app.current_organization_id`.
- **Resource Discovery & Catalog**: Search, category filters, specifications, location, hourly rates, and real-time status.
- **Safety Eligibility Gates**: Server-side enforcement of active safety permits and certified operator training qualifications before booking (e.g. Agilent 1290 UHPLC-MS enforces certified clearance).
- **Reservation Lifecycle & Concurrency**: PostgreSQL locking (`FOR UPDATE`) to prevent overlapping time-slots, cancellation reason tracking, and manager approval queues.
- **Check-In & Return Handover Gate**: Pre-use and post-use mandatory condition checklists, discrepancy/incident notes, session transition to `in_use` and `completed`.
- **Private Evidence Storage**: Private Supabase Storage bucket integration (`sharespace-evidence`) with file MIME/magic-byte validation, file size enforcement (<10MB), opaque tenant-isolated object keys, and short-lived signed access URLs.
- **Append-Only Audit Trail**: Immutable logging of all security, reservation, handover, qualification, and evidence operations.

---

## 9. Clean Machine Setup Guide

### 1. Extract ZIP
```bash
unzip ShareSpace_Final.zip -d sharespace_app
cd sharespace_app/sharespace
```

### 2. Configure Environment Files
```bash
# Backend configuration
cp backend/.env.example backend/.env

# Frontend configuration
cp frontend/.env.example frontend/.env
```
Populate `backend/.env` with your PostgreSQL database URL, Supabase project URL, and Supabase Storage credentials (`SUPABASE_SERVICE_ROLE_KEY` and `EVIDENCE_STORAGE_BUCKET`).

### 3. Backend Setup & Run
```bash
cd backend
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run database migrations
uv run alembic upgrade head

# Run automated tests (114 tests)
uv run pytest

# Start development server
uv run uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup & Run
```bash
cd ../frontend
npm install

# Run tests, linter, and production build
npm test -- --run
npm run lint
npm run build

# Start frontend dev server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.
