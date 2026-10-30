# ShareSpace — Resource-Sharing Platform for Campus Communities

> Unlock underused equipment and spaces for colleges, research laboratories and institutional communities.

ShareSpace is a multi-tenant platform that makes specialised institutional assets (confocal microscopes, 3D printers, FTIR spectrometers, seminar halls, AV equipment) easy to discover, fairly allocated and safely handed over.

---

## 🔗 Live Demo

| | Link |
|---|---|
| **Frontend (Vercel)** | https://share-space-neon.vercel.app/ |
| **Backend API (Render)** | https://sharespace-ruhq.onrender.com/api/v1 |
| **API Docs (Swagger)** | https://sharespace-ruhq.onrender.com/api/v1/docs |

> ⏳ **Note:** the backend runs on a free Render instance, which sleeps when idle. The **first request can take 30–60 seconds** to wake it. Please wait and refresh once if the header shows "API offline" at first.

---

## 🔑 Demo Credentials

Use these test accounts to explore each role. Sign in from the **Sign In** button on the site.

| Role | Email | Password |
|---|---|---|
| 🎓 **Student** | `student@test.com` | `Pass@12345` |
| 🧪 **Lab Manager** | `manager@test.com` | `Pass@12345` |
| 🛡️ **Admin** | `admin@test.com` | `Pass@12345` |

> These are throwaway accounts created only for demonstration. They hold no real data.

### What each role can try

- **Student:** browse the resource catalogue, open a resource, request a booking, view *My Bookings*.
- **Lab Manager:** review and approve or reject booking requests, manage resources and availability windows.
- **Admin:** manage members and roles, view audit logs, oversee the whole organisation.

---

## ✨ Key Features

- **Resource discovery:** searchable catalogue of labs, workshops, seminar spaces and cameras/AV gear, filtered by category.
- **Strict booking integrity:** double-booking is prevented at the database level using PostgreSQL range-exclusion constraints.
- **Approval workflow:** bookings are reviewed by authorised lab managers.
- **Mandatory handover verification:** written condition checklists and photographic evidence at check-in and return.
- **Fair use:** weekly quotas and cooldown periods stop any one user from monopolising equipment.
- **Safety permits and qualifications:** access to sensitive equipment is gated by verified permits.
- **Incident reporting and review:** every incident or damage report is reviewed by a human manager.
- **Role-based access control and audit trail:** every sensitive action is logged.
- **Row-level security:** tenant data is isolated at the database layer.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, React Router v7 |
| **Backend** | Python, FastAPI, Pydantic v2 |
| **Database / ORM** | PostgreSQL (Supabase), SQLAlchemy 2.0 (asyncpg), Alembic migrations |
| **Auth & Storage** | Supabase Auth (JWT) and Supabase Storage (private evidence bucket) |
| **Hosting** | Vercel (frontend), Render (backend), Supabase (database) |
| **Testing** | Pytest, pytest-asyncio |

---

## 🏗️ Architecture

```
┌────────────────────┐   HTTPS + JWT   ┌────────────────────┐   asyncpg   ┌───────────────────┐
│  React + Vite SPA  │ ──────────────► │   FastAPI backend  │ ──────────► │ Supabase Postgres │
│     (Vercel)       │                 │      (Render)      │             │  + Storage + Auth │
└─────────┬──────────┘                 └────────────────────┘             └───────────────────┘
          │  sign-in / sign-up                                                      ▲
          └─────────────────────────────  Supabase Auth  ───────────────────────────┘
```

1. The user signs in through **Supabase Auth** and receives a JWT.
2. The frontend sends that JWT to the **FastAPI** backend.
3. The backend verifies the token, checks the user's organisation role, and reads or writes PostgreSQL.

---

## 📁 Repository Structure

```text
sharespace/
├── frontend/            # React + Vite + TypeScript app
│   └── src/             # api client, components, routes, context
├── backend/             # FastAPI service
│   ├── app/             # api/v1 endpoints, core config, db, models, schemas, services, scripts
│   ├── migrations/      # Alembic migrations
│   └── tests/           # Pytest suite
└── docs/                # Architecture notes
```

---

## 💻 Run Locally

### Prerequisites
- Node.js 20+ (22 recommended)
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- A [Supabase](https://supabase.com) project (Postgres, Auth and a private Storage bucket named `sharespace-evidence`)

### 1. Clone

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO
```

### 2. Backend

```bash
cd backend
cp .env.example .env          # then fill in your values
uv sync
uv run alembic upgrade head   # create tables, roles and RLS policies
uv run uvicorn app.main:app --reload --port 8000
```

Key backend variables (see `backend/.env.example` for the full list):

```env
DATABASE_URL=postgresql+asyncpg://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SECRET_KEY=<long-random-string>
CORS_ORIGINS=http://localhost:5173
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://<ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon-key>
```

Open http://localhost:5173.

### 4. First-time data setup

The app needs an organisation and member roles before sign-in is useful:

```sql
-- run once in the Supabase SQL Editor
INSERT INTO organizations (id, name, slug, domain, is_active, settings_json)
VALUES (gen_random_uuid(), 'Apex Institute of Technology', 'apex-institute', 'apex.edu', true,
        '{"campus": "Main Campus", "allow_guest_browse": true}')
ON CONFLICT (slug) DO NOTHING;
```

Sign in once with each user, then assign roles and load sample resources:

```bash
cd backend
uv run python -m app.scripts.manage_membership assign --email admin@test.com   --org-slug apex-institute --role admin
uv run python -m app.scripts.manage_membership assign --email manager@test.com --org-slug apex-institute --role lab_manager
uv run python -m app.scripts.manage_membership assign --email student@test.com --org-slug apex-institute --role student
uv run python -m app.scripts.seed_resources
```

---

## ☁️ Deployment

| Part | Platform | Key settings |
|---|---|---|
| Frontend | Vercel | Root `frontend`, framework Vite, output `dist`, env `VITE_*` |
| Backend | Render | Root `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Database | Supabase | Session-pooler connection string, private storage bucket |

A `frontend/vercel.json` rewrite sends all routes to `index.html` so client-side routing survives a page refresh. In production the backend must have `CORS_ORIGINS` set to the exact frontend URL.

---

## 🧪 Running Tests

```bash
cd backend
uv run pytest
```

---

## 🩺 Health Checks

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/health` | Is the API running? |
| `GET /api/v1/ready` | Is the database reachable? |
| `GET /api/v1/docs` | Interactive Swagger documentation |

The header of the web app also shows live **API** and **DB** status indicators.

---

## 👤 Author

**Purvesh**: B.Tech, Mechanical Engineering, IIT Patna

---

## 📄 License

Add your licence here (for example MIT), or remove this section.
