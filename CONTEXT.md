# FX Trade Simulation Server - Context Document

## Overview
This is a Python FastAPI application converted from Java Spring Boot. It simulates foreign exchange (FX) trading with configurable time intervals.

## Tech Stack
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL with SQLAlchemy ORM (async)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Testing**: pytest with pytest-asyncio

## Quick Start

### 1. Start PostgreSQL
```bash
docker-compose up -d db
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
```bash
cp .env.example .env
# Or set directly:
export DATABASE_URL=postgresql+asyncpg://fxtrade:fxtrade@localhost:5432/fxtrade
export DATABASE_URL_SYNC=postgresql://fxtrade:fxtrade@localhost:5432/fxtrade
```

### 4. Run Migrations
```bash
alembic upgrade head
```

### 5. Initialize Sample Data
```bash
python scripts/init_db.py
```

### 6. Start Server
```bash
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Scenario API (`/api/scenario`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all scenarios |
| GET | `/{name}` | Get scenario by name |
| POST | `/` | Create new scenario |
| PUT | `/{name}` | Update scenario |
| DELETE | `/{name}` | Delete scenario |

### Rate API (`/api/rate`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{timestamp}` | Get rates at timestamp |
| GET | `/{timestamp}?nearest=true` | Get nearest available rates |
| POST | `/bulk` | Bulk upload rates |

### Trade API (`/api/trade`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/start/{scenario}/{user_id}` | Start trading session |
| POST | `/next` | Execute trades & advance time |
| GET | `/session/{session_id}` | Get session details |
| GET | `/sessions/{user_id}` | Get user's sessions |

## Example API Calls

### Create a Scenario
```bash
curl -X POST http://localhost:8000/api/scenario \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TEST_5MIN",
    "start_datetime": "2016-01-04T09:00:00",
    "end_datetime": "2016-01-04T17:00:00",
    "time_interval_seconds": 300,
    "initial_balance": 1000000,
    "commission_rate": 0
  }'
```

### Upload Rates
```bash
curl -X POST http://localhost:8000/api/rate/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "rates": [
      {"currency": "USD", "timestamp": "2016-01-04T09:00:00", "rate_to_jpy": 118.25},
      {"currency": "EUR", "timestamp": "2016-01-04T09:00:00", "rate_to_jpy": 128.50}
    ]
  }'
```

### Start a Session
```bash
curl -X POST http://localhost:8000/api/trade/start/TEST_5MIN/testuser
```

### Execute Trade and Advance Time
```bash
curl -X POST http://localhost:8000/api/trade/next \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "exchange_requests": [
      {"currency_from": "JPY", "currency_to": "USD", "amount": 100000}
    ]
  }'
```

## Database Schema

### Tables
1. **scenarios** - Trading scenario configurations (name, start/end datetime, time_interval_seconds, commission_rate, initial_balance)
2. **traders** - User entities (user_id, type: 'prod'|'test')
3. **trading_sessions** - Active/completed trading sessions
4. **balances** - Currency balance snapshots at each timestamp
5. **rates** - Exchange rates (currency to JPY) at timestamps

## Project Structure
```
fxtrade-server/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings
│   ├── database.py          # DB connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routes
│   ├── services/            # Business logic
│   └── utils/               # Utilities
├── alembic/                 # Migrations
├── data/                    # CSV data files
├── tests/                   # Test files
├── scripts/                 # Init & import scripts
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_trade_api.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Key Concepts

### Time Intervals
- `time_interval_seconds` determines how much time advances per `/next` call
- 86400 = 1 day, 3600 = 1 hour, 300 = 5 minutes

### Rate Lookup
- Rates are stored with timestamps
- When querying, uses nearest available rate <= current time

### Trading Flow
1. Create a scenario with time range and interval
2. Upload exchange rates for the time period
3. Start a session for a user
4. Call `/next` to execute trades and advance time
5. Session completes when `current_datetime >= end_datetime`

## Supported Currencies
JPY, USD, EUR, GBP, AUD, CHF, CNY, HKD
