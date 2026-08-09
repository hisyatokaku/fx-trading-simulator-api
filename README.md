# FX Trade Simulation Server

A FastAPI server that simulates foreign exchange trading. Participants write Python programs to call the API, execute trades, and maximise their final JPY balance.

## Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL via SQLAlchemy (async) + Alembic migrations
- **Runtime**: Python 3.12

## Quick Start (local)

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Start server

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### 6. Seed data

```bash
# Upserts scenarios.csv, traders.csv and rates.csv via the live API
python scripts/seed_data.py
```

---

## Docker (full stack)

```bash
docker compose up --build
```

---

## Production

- API: http://34.146.231.219:8000
- Swagger UI: http://34.146.231.219:8000/docs

### Seeding scenarios.csv / traders.csv / rates.csv

Data seeding is independent of migrations, and can be re-run anytime data/*.csv changes — it upserts via the live API (`/api/scenario/bulk`, `/api/trader/bulk`, `/api/rate/bulk`), not the database directly, so it never gets out of sync with a schema change:

```bash
python scripts/seed_data.py http://34.146.231.219:8000
```

---

## Project Structure

```
fx-trading-simulator-api/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings (env vars)
│   ├── database.py          # Async DB engine & session
│   ├── api/                 # Route handlers
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic
│   └── utils/               # RateMatrix, date helpers
├── alembic/                 # DB migrations
├── data/                    # June 2026 scenarios, traders, and one-minute rates
├── document/                # Participant guide (Jupyter notebook)
├── scripts/
│   ├── generate_rates.py    # Generate optional data/rates_2016.csv demo data
│   ├── seed_data.py         # Upsert scenarios/traders/rates via the live API
│   └── verify_scenario.py   # End-to-end correctness test
└── tests/                   # pytest test suite
```

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scenario/` | List all scenarios |
| POST | `/api/scenario/` | Create scenario |
| POST | `/api/scenario/bulk` | Bulk upsert scenarios |
| POST | `/api/scenario/{id}/check-rates` | Check rate coverage for a scenario |
| GET | `/api/rate/{datetime}` | Get rates at exact datetime |
| POST | `/api/rate/bulk` | Bulk upsert rates |
| POST | `/api/trader/bulk` | Bulk upsert traders |
| POST | `/api/trade/start/{scenario}/{user_id}` | Start a trading session |
| POST | `/api/trade/next` | Execute trades and advance time |
| GET | `/api/trade/session/{session_id}` | Get session details |
| GET | `/api/trade/sessions/{user_id}` | Get all sessions for a user |

---

## Running Tests

```bash
pytest tests/ -v
```

## Verifying a Scenario End-to-End

```bash
python scripts/verify_scenario.py                          # DEMO_5MIN (default)
python scripts/verify_scenario.py DEMO_3DAY testuser
python scripts/verify_scenario.py DEMO_5MIN testuser http://your-server.com
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://fxtrade:fxtrade@localhost:5432/fxtrade` | Async DB URL |
| `DATABASE_URL_SYNC` | `postgresql://fxtrade:fxtrade@localhost:5432/fxtrade` | Sync DB URL (Alembic) |
| `APP_ENV` | `development` | Environment name |
| `DEBUG` | `true` | Enable debug logging |
