# Baseerah — Backend (FastAPI)

AI-powered utility consumption intelligence. Phase 1 MVP backend: bill ingestion,
baseline + anomaly/leak detection, and simple forecasting.

## Stack
- **FastAPI** (API) · **SQLAlchemy 2.0** (ORM) · **Pydantic v2** (validation)
- **SQLite** for dev (Postgres-ready — set `BASEERAH_DATABASE_URL`)
- Analysis engine is pure-Python (`statistics`) — no heavy ML deps yet

## Setup

```bash
cd backend
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# bash/zsh:            source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open interactive API docs at http://127.0.0.1:8000/docs

## Test

```bash
pytest
```

> **Dev note:** for zero-setup local dev the app calls `create_all` on startup, which does
> **not** alter existing tables. After changing a model in dev, either delete the dev DB
> (`rm baseerah.db`) or run the migrations below. For any real database, migrations are authoritative.

## Migrations (Alembic)

```bash
# apply all migrations to the configured database
alembic upgrade head

# after changing a model, generate a migration
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Alembic reads the DB URL from `BASEERAH_DATABASE_URL` (via `alembic/env.py`), so it targets
the same database as the app. Migrations live in `alembic/versions/`.

## Auth

All data endpoints require a Bearer token. Register → login → use the token.
In Swagger (`/docs`) click **Authorize** and log in with your email + password.

## Try the flow (quickstart)

```bash
# 1. register
curl -X POST localhost:8000/auth/register -H "content-type: application/json" \
  -d '{"email":"a@b.com","name":"Test","password":"password123"}'

# 2. login (form-encoded; username = email) -> copy access_token
curl -X POST localhost:8000/auth/login \
  -d "username=a@b.com&password=password123"
TOKEN=...   # paste access_token here

# 3. add a property
curl -X POST localhost:8000/properties -H "content-type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Home","type":"villa","region":"Muscat"}'

# 4. add a few monthly water bills for property 1
curl -X POST localhost:8000/properties/1/bills -H "content-type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"utility_type":"water","period_start":"2026-01-01","period_end":"2026-01-31","consumption":10,"cost":5}'
# ...repeat for more months, then spike the latest to see a leak flagged

# 5. analyze
curl -H "Authorization: Bearer $TOKEN" \
  "localhost:8000/properties/1/analysis?utility_type=water"
```

## Layout

```
app/
  main.py            # app factory + router wiring
  config.py          # settings (env: BASEERAH_*)
  database.py        # engine, session, Base, init_db
  security.py        # password hashing (PBKDF2) + JWT issue/verify
  models/            # SQLAlchemy models: User, Property, Bill
  schemas/           # Pydantic request/response models
  services/
    analysis.py      # core engine: baseline, anomaly, leak, forecast, recommendations
  api/
    deps.py          # get_current_user, ownership guard
    routes/          # health, auth, properties, bills, analysis
tests/
  conftest.py        # isolated in-memory DB + client fixtures
  test_analysis.py   # table-driven tests for the analysis engine
  test_auth.py       # auth + per-user authorization
```

## Done
- Auth (JWT) + per-user authorization
- Analysis engine (baseline, anomaly, leak, forecast, recommendations)
- LLM explanation layer (Claude) — phrases the numbers, never invents them (`BASEERAH_ANTHROPIC_API_KEY`)
- Alembic migrations
- Frontend (Vite + React, bilingual AR/EN, charts)

## Roadmap (not yet built)
- OCR bill upload (PDF/image) → parsing (needs Tesseract or a cloud OCR service)
- ML anomaly detection + weather-adjusted forecasting (needs labeled data + a weather API)
- Auth hardening: migrate PBKDF2 → argon2/bcrypt, refresh tokens, rate-limiting
