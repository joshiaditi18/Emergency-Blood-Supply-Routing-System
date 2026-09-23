# Emergency Blood Supply Routing System

The Emergency Blood Supply Routing System is a Flask + SQLAlchemy backend with a React + TypeScript + Vite + Tailwind frontend, relational models, manual routing/allocation algorithms, secure authentication, and fictional demo data.

The algorithm modules are interfaces only in this phase. BFS, Red-Black Tree priority management, Greedy allocation, and A* pathfinding will be implemented and integrated in later approved phases. No algorithm outputs are fabricated.

## Structure

- `frontend/` React, TypeScript, Vite, Tailwind shell
- `backend/` Flask application, models, services, security, routes, algorithms, migrations
- `tests/` Phase 1 smoke tests
- `docs/` architecture and phase notes

## Requirements

- Python 3.12+
- Node.js 22+
- Python 3.12+
- Node.js 22+
- No database server is required for local development; SQLite is the development database.

## Local setup

1. Create environment files:

   `Copy-Item backend/.env.example backend/.env`

   Set a real `DEMO_ADMIN_PASSWORD` in `backend/.env` before seeding. Keep `.env` uncommitted.

2. Install backend dependencies and create the virtual environment:

   `python -m venv .venv`

   `\.venv\Scripts\Activate.ps1`

   `pip install -r backend/requirements.txt`

3. Run the SQLite migration:

   `flask --app backend/run.py db upgrade`

4. Load fictional demo data:

   `$env:DEMO_ADMIN_PASSWORD = 'choose-a-local-demo-password'`

   `flask --app backend/manage.py seed`

5. Start Flask:

   `flask --app backend/run.py run --debug --port 5000`

   Health check: `http://localhost:5000/api/health`

6. Start React in another terminal:

   `Set-Location frontend`

   `npm install`

   `npm run dev`

   Frontend: `http://localhost:5173`

## Database targets

**Development database: SQLite**

The default `DATABASE_URL` is `sqlite:///blood_supply_dev.db`. Migrations, seed data, tests, and local Flask startup work without PostgreSQL, Docker, or an external database service.

**PostgreSQL: optional production target**

SQLAlchemy keeps the application database-agnostic. PostgreSQL may be configured later with a PostgreSQL `DATABASE_URL`, but it is not required for local development and was not used for the local verification in this repository.

SQLite does not provide PostgreSQL-equivalent row-lock behavior. The allocation workflow keeps `with_for_update()` and transaction revalidation for production-compatible database engines; SQLite tests verify workflow correctness and non-negative inventory, not PostgreSQL concurrency semantics.

## Phase 1 database

The initial migration creates: `users`, `hospitals`, `hospital_connections`, `blood_inventory`, `blood_inventory_transactions`, `blood_requests`, `allocations`, `routes`, `dispatches`, `audit_logs`, and `notifications`.

## Security baseline

Phase 2 provides Argon2id password hashing, JWT access and refresh tokens, persistent token revocation, backend RBAC, AES-256-GCM utilities, explicit CORS, security headers, configurable authentication rate limits, validation helpers, centralized JSON errors, and security audit events. Secrets and database credentials remain environment-only.

Authentication endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/auth/admin-check` (RBAC verification endpoint)

Copy `backend/.env.example` to `backend/.env` and set `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY`, `ENCRYPTION_KEY`, `DATABASE_URL`, and `DEMO_ADMIN_PASSWORD` to local values. The encryption key must be URL-safe base64 for 32 random bytes.

## Testing

From the repository root with the virtual environment active:

`pytest`

The SQLite test suite covers health, authentication, RBAC, password handling, encryption integrity, validation, rate limiting, headers, audit behavior, BFS, Red-Black Tree priority, Greedy allocation, A*, request creation, blood compatibility, inventory updates, insufficient inventory, competing requests, non-negative inventory, multi-donor allocation, and dispatch creation.
