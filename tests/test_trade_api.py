"""Tests for Trade API endpoints."""

import pytest
from httpx import AsyncClient


async def setup_scenario_and_rates(client: AsyncClient, scenario_name: str = "TRADE_TEST"):
    """Helper to set up scenario and rates for trading tests."""
    # Create scenario
    await client.post(
        "/api/scenario/",
        json={
            "name": scenario_name,
            "start_datetime": "2016-01-04T00:00:00",
            "end_datetime": "2016-01-08T00:00:00",
            "time_interval_seconds": 86400,
            "initial_balance": 1000000,
        }
    )

    # Upload rates
    await client.post(
        "/api/rate/bulk",
        json={
            "rates": [
                {"currency": "USD", "timestamp": "2016-01-04T00:00:00", "rate_to_jpy": "118.25"},
                {"currency": "EUR", "timestamp": "2016-01-04T00:00:00", "rate_to_jpy": "128.50"},
                {"currency": "USD", "timestamp": "2016-01-05T00:00:00", "rate_to_jpy": "118.50"},
                {"currency": "EUR", "timestamp": "2016-01-05T00:00:00", "rate_to_jpy": "128.75"},
                {"currency": "USD", "timestamp": "2016-01-06T00:00:00", "rate_to_jpy": "118.00"},
                {"currency": "EUR", "timestamp": "2016-01-06T00:00:00", "rate_to_jpy": "128.25"},
                {"currency": "USD", "timestamp": "2016-01-07T00:00:00", "rate_to_jpy": "119.00"},
                {"currency": "EUR", "timestamp": "2016-01-07T00:00:00", "rate_to_jpy": "129.00"},
                {"currency": "USD", "timestamp": "2016-01-08T00:00:00", "rate_to_jpy": "119.50"},
                {"currency": "EUR", "timestamp": "2016-01-08T00:00:00", "rate_to_jpy": "129.25"},
            ]
        }
    )


@pytest.mark.asyncio
async def test_start_session(client: AsyncClient):
    """Test starting a new trading session."""
    await setup_scenario_and_rates(client, "START_TEST")

    response = await client.post("/api/trade/start/START_TEST/testuser")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "testuser"
    assert data["scenario_name"] == "START_TEST"
    assert data["is_complete"] is False
    assert "JPY" in data["balances"]
    assert float(data["balances"]["JPY"]) == 1000000


@pytest.mark.asyncio
async def test_start_session_scenario_not_found(client: AsyncClient):
    """Test starting session with non-existent scenario."""
    response = await client.post("/api/trade/start/NONEXISTENT/testuser")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_execute_trade(client: AsyncClient):
    """Test executing a trade and advancing time."""
    await setup_scenario_and_rates(client, "EXECUTE_TEST")

    # Start session
    start_response = await client.post("/api/trade/start/EXECUTE_TEST/trader1")
    session_id = start_response.json()["id"]

    # Execute trade: buy USD with JPY
    response = await client.post(
        "/api/trade/next",
        json={
            "session_id": session_id,
            "exchange_requests": [
                {"currency_from": "JPY", "currency_to": "USD", "amount": "100000"}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["trades"]) == 1
    assert data["trades"][0]["currency_from"] == "JPY"
    assert data["trades"][0]["currency_to"] == "USD"
    assert float(data["balances"]["JPY"]) < 1000000
    assert float(data["balances"]["USD"]) > 0


@pytest.mark.asyncio
async def test_advance_without_trade(client: AsyncClient):
    """Test advancing time without making any trades."""
    await setup_scenario_and_rates(client, "ADVANCE_TEST")

    # Start session
    start_response = await client.post("/api/trade/start/ADVANCE_TEST/trader2")
    session_id = start_response.json()["id"]

    # Advance without trades
    response = await client.post(
        "/api/trade/next",
        json={
            "session_id": session_id,
            "exchange_requests": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["trades"]) == 0
    # Balances should remain unchanged
    assert float(data["balances"]["JPY"]) == 1000000


@pytest.mark.asyncio
async def test_session_completion(client: AsyncClient):
    """Test session completes when reaching end datetime."""
    await setup_scenario_and_rates(client, "COMPLETE_TEST")

    # Start session
    start_response = await client.post("/api/trade/start/COMPLETE_TEST/trader3")
    session_id = start_response.json()["id"]

    # Advance through all days
    for _ in range(5):  # 4 days + extra to ensure completion
        response = await client.post(
            "/api/trade/next",
            json={"session_id": session_id, "exchange_requests": []}
        )
        if response.json()["is_complete"]:
            break

    assert response.json()["is_complete"] is True


@pytest.mark.asyncio
async def test_trade_on_completed_session(client: AsyncClient):
    """Test trading on completed session fails."""
    await setup_scenario_and_rates(client, "COMPLETED_TEST")

    # Start session
    start_response = await client.post("/api/trade/start/COMPLETED_TEST/trader4")
    session_id = start_response.json()["id"]

    # Complete the session
    for _ in range(5):
        response = await client.post(
            "/api/trade/next",
            json={"session_id": session_id, "exchange_requests": []}
        )
        if response.json()["is_complete"]:
            break

    # Try to trade on completed session
    response = await client.post(
        "/api/trade/next",
        json={"session_id": session_id, "exchange_requests": []}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_advance_into_missing_rate_gap(client: AsyncClient):
    """Advancing into a timestamp with no rate data should 404, not crash with a 500."""
    await client.post(
        "/api/scenario/",
        json={
            "name": "GAP_TEST",
            "start_datetime": "2016-01-04T00:00:00",
            "end_datetime": "2016-01-06T00:00:00",
            "time_interval_seconds": 86400,
            "initial_balance": 1000000,
        }
    )
    # Only seed a rate for the start day, not for the next step.
    await client.post(
        "/api/rate/bulk",
        json={"rates": [{"currency": "USD", "timestamp": "2016-01-04T00:00:00", "rate_to_jpy": "118.25"}]}
    )

    start_response = await client.post("/api/trade/start/GAP_TEST/gap_trader")
    session_id = start_response.json()["id"]

    # First call succeeds using day-1 rates, then advances current_datetime to day 2.
    first = await client.post(
        "/api/trade/next",
        json={"session_id": session_id, "exchange_requests": []}
    )
    assert first.status_code == 200

    # Second call needs day-2 rates, which were never seeded.
    second = await client.post(
        "/api/trade/next",
        json={"session_id": session_id, "exchange_requests": []}
    )
    assert second.status_code == 404


@pytest.mark.asyncio
async def test_get_session(client: AsyncClient):
    """Test getting session details."""
    await setup_scenario_and_rates(client, "GET_SESSION_TEST")

    # Start session
    start_response = await client.post("/api/trade/start/GET_SESSION_TEST/trader5")
    session_id = start_response.json()["id"]

    # Get session
    response = await client.get(f"/api/trade/session/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["user_id"] == "trader5"


@pytest.mark.asyncio
async def test_get_session_history(client: AsyncClient):
    """Test getting all balance snapshots for a session."""
    await setup_scenario_and_rates(client, "HISTORY_TEST")

    start_response = await client.post("/api/trade/start/HISTORY_TEST/history_trader")
    session_id = start_response.json()["id"]
    await client.post(
        "/api/trade/next",
        json={"session_id": session_id, "exchange_requests": []},
    )

    response = await client.get(f"/api/trade/session/{session_id}/history")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["scenario_name"] == "HISTORY_TEST"
    assert list(data["balance_history"]) == [
        "2016-01-04T00:00:00",
        "2016-01-05T00:00:00",
    ]
    assert data["balance_history"]["2016-01-04T00:00:00"]["JPY"] == 1000000


@pytest.mark.asyncio
async def test_get_session_history_not_found(client: AsyncClient):
    """Test getting history for a non-existent session."""
    response = await client.get("/api/trade/session/99999/history")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient):
    """Test getting non-existent session."""
    response = await client.get("/api/trade/session/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_sessions(client: AsyncClient):
    """Test getting all sessions for a user."""
    await setup_scenario_and_rates(client, "USER_SESSIONS_TEST")

    # Start multiple sessions
    await client.post("/api/trade/start/USER_SESSIONS_TEST/multiuser")
    await client.post("/api/trade/start/USER_SESSIONS_TEST/multiuser")

    # Get user sessions
    response = await client.get("/api/trade/sessions/multiuser")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert all(s["user_id"] == "multiuser" for s in data["sessions"])


@pytest.mark.asyncio
async def test_convert_entire_balance_is_not_dropped(client: AsyncClient):
    """An order for exactly the caller's full balance must execute, not be skipped.

    Balances are stored as Decimal but reported over JSON as float. Comparing the
    stored Decimal against the raw float expands the float to its exact binary
    value (8456.659619 -> 8456.65961900000002060551196336746215820312), which
    reads as larger than the balance -- so every "convert everything" order was
    silently dropped with no trade and no error.
    """
    await setup_scenario_and_rates(client, "FULL_BALANCE_TEST")

    start_response = await client.post("/api/trade/start/FULL_BALANCE_TEST/fulltrader")
    session_id = start_response.json()["id"]

    # Spend the entire JPY balance on USD.
    response = await client.post(
        "/api/trade/next",
        json={
            "session_id": session_id,
            "exchange_requests": [
                {"currency_from": "JPY", "currency_to": "USD", "amount": 1000000}
            ],
        },
    )
    assert response.status_code == 200
    usd_balance = response.json()["balances"]["USD"]
    assert usd_balance > 0

    # Sell it all back, quoting the balance exactly as the API just reported it.
    response = await client.post(
        "/api/trade/next",
        json={
            "session_id": session_id,
            "exchange_requests": [
                {"currency_from": "USD", "currency_to": "JPY", "amount": usd_balance}
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trades"], "full-balance order was silently dropped"
    assert data["balances"]["USD"] == pytest.approx(0.0, abs=1e-6)
    assert data["balances"]["JPY"] > 0


@pytest.mark.asyncio
async def test_order_a_hair_above_the_balance_still_executes(client: AsyncClient):
    """Sub-quantum overshoot must not drop the order, but a real one still must.

    Callers size a "sell everything" order as balance * rate / rate, which lands
    a fraction of a ulp either side of the balance. Balances are Numeric(20, 6),
    so an overshoot below 1e-6 is noise, not insufficient funds.
    """
    await setup_scenario_and_rates(client, "EPSILON_TEST")

    start_response = await client.post("/api/trade/start/EPSILON_TEST/epsilontrader")
    session_id = start_response.json()["id"]

    response = await client.post(
        "/api/trade/next",
        json={
            "session_id": session_id,
            "exchange_requests": [
                {"currency_from": "JPY", "currency_to": "USD", "amount": 1000000}
            ],
        },
    )
    usd_balance = response.json()["balances"]["USD"]

    # A hair over the balance, well inside the 1e-6 storage quantum.
    response = await client.post(
        "/api/trade/next",
        json={
            "session_id": session_id,
            "exchange_requests": [
                {"currency_from": "USD", "currency_to": "JPY", "amount": usd_balance + 1e-9}
            ],
        },
    )
    assert response.json()["trades"], "sub-quantum overshoot was dropped"

    # Genuinely more than the caller holds is still refused.
    response = await client.post(
        "/api/trade/next",
        json={
            "session_id": session_id,
            "exchange_requests": [
                {"currency_from": "USD", "currency_to": "JPY", "amount": 1000.0}
            ],
        },
    )
    assert response.json()["trades"] == []
