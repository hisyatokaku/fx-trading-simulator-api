"""Tests for Scenario API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_scenario(client: AsyncClient):
    """Test creating a new scenario."""
    response = await client.post(
        "/api/scenario/",
        json={
            "name": "NEW_SCENARIO",
            "start_datetime": "2016-01-04T00:00:00",
            "end_datetime": "2016-12-30T00:00:00",
            "time_interval_seconds": 86400,
            "game_type": "ANY",
            "initial_balance": 1000000,
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "NEW_SCENARIO"
    assert data["time_interval_seconds"] == 86400


@pytest.mark.asyncio
async def test_create_scenario_duplicate(client: AsyncClient):
    """Test creating a duplicate scenario fails."""
    # Create first scenario
    await client.post(
        "/api/scenario/",
        json={
            "name": "DUPLICATE",
            "start_datetime": "2016-01-04T00:00:00",
            "end_datetime": "2016-12-30T00:00:00",
            "time_interval_seconds": 86400,
        }
    )

    # Try to create duplicate
    response = await client.post(
        "/api/scenario/",
        json={
            "name": "DUPLICATE",
            "start_datetime": "2016-01-04T00:00:00",
            "end_datetime": "2016-12-30T00:00:00",
            "time_interval_seconds": 86400,
        }
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_scenario(client: AsyncClient):
    """Test getting a scenario by name."""
    # Create scenario
    await client.post(
        "/api/scenario/",
        json={
            "name": "GET_TEST",
            "start_datetime": "2016-01-04T00:00:00",
            "end_datetime": "2016-12-30T00:00:00",
            "time_interval_seconds": 3600,
        }
    )

    # Get it
    response = await client.get("/api/scenario/GET_TEST")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "GET_TEST"
    assert data["time_interval_seconds"] == 3600


@pytest.mark.asyncio
async def test_get_scenario_not_found(client: AsyncClient):
    """Test getting a non-existent scenario."""
    response = await client.get("/api/scenario/NONEXISTENT")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_scenario_rates(client: AsyncClient):
    """Test getting rates only at timestamps visited by a scenario."""
    await client.post(
        "/api/scenario/",
        json={
            "name": "RATES_TEST",
            "start_datetime": "2016-01-04T00:00:00",
            "end_datetime": "2016-01-06T00:00:00",
            "time_interval_seconds": 86400,
        },
    )
    await client.post(
        "/api/rate/bulk",
        json={
            "rates": [
                {"currency": "USD", "timestamp": "2016-01-04T00:00:00", "rate_to_jpy": "118.25"},
                {"currency": "EUR", "timestamp": "2016-01-04T00:00:00", "rate_to_jpy": "128.50"},
                {"currency": "USD", "timestamp": "2016-01-04T12:00:00", "rate_to_jpy": "999.00"},
                {"currency": "USD", "timestamp": "2016-01-05T00:00:00", "rate_to_jpy": "118.50"},
                {"currency": "USD", "timestamp": "2016-01-06T00:00:00", "rate_to_jpy": "118.75"},
            ]
        },
    )

    response = await client.get("/api/scenario/RATES_TEST/rates")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "RATES_TEST"
    assert list(data["date_to_currency_pair_to_rate"]) == [
        "2016-01-04T00:00:00",
        "2016-01-05T00:00:00",
        "2016-01-06T00:00:00",
    ]
    assert data["date_to_currency_pair_to_rate"]["2016-01-04T00:00:00"] == {
        "EUR/JPY": 128.5,
        "USD/JPY": 118.25,
    }


@pytest.mark.asyncio
async def test_get_scenario_rates_not_found(client: AsyncClient):
    """Test getting rates for a non-existent scenario."""
    response = await client.get("/api/scenario/NONEXISTENT/rates")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_scenarios(client: AsyncClient):
    """Test listing all scenarios."""
    # Create some scenarios
    for name in ["LIST_A", "LIST_B", "LIST_C"]:
        await client.post(
            "/api/scenario/",
            json={
                "name": name,
                "start_datetime": "2016-01-04T00:00:00",
                "end_datetime": "2016-12-30T00:00:00",
                "time_interval_seconds": 86400,
            }
        )

    response = await client.get("/api/scenario/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    names = [s["name"] for s in data]
    assert "LIST_A" in names
    assert "LIST_B" in names
    assert "LIST_C" in names


@pytest.mark.asyncio
async def test_update_scenario(client: AsyncClient):
    """Test updating a scenario."""
    # Create scenario
    await client.post(
        "/api/scenario/",
        json={
            "name": "UPDATE_TEST",
            "start_datetime": "2016-01-04T00:00:00",
            "end_datetime": "2016-12-30T00:00:00",
            "time_interval_seconds": 86400,
        }
    )

    # Update it
    response = await client.put(
        "/api/scenario/UPDATE_TEST",
        json={
            "time_interval_seconds": 3600,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["time_interval_seconds"] == 3600


@pytest.mark.asyncio
async def test_delete_scenario(client: AsyncClient):
    """Test deleting a scenario."""
    # Create scenario
    await client.post(
        "/api/scenario/",
        json={
            "name": "DELETE_TEST",
            "start_datetime": "2016-01-04T00:00:00",
            "end_datetime": "2016-12-30T00:00:00",
            "time_interval_seconds": 86400,
        }
    )

    # Delete it
    response = await client.delete("/api/scenario/DELETE_TEST")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get("/api/scenario/DELETE_TEST")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bulk_upload_scenarios(client: AsyncClient):
    """Test bulk uploading scenarios."""
    response = await client.post(
        "/api/scenario/bulk",
        json={
            "scenarios": [
                {
                    "name": "BULK_A",
                    "start_datetime": "2016-01-04T00:00:00",
                    "end_datetime": "2016-12-30T00:00:00",
                    "time_interval_seconds": 86400,
                    "game_type": "ANY",
                    "initial_balance": 1000000,
                },
                {
                    "name": "BULK_B",
                    "start_datetime": "2016-01-04T09:00:00",
                    "end_datetime": "2016-01-04T17:00:00",
                    "time_interval_seconds": 300,
                    "game_type": "ANY",
                    "initial_balance": 1000000,
                },
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 2
    assert data["updated"] == 0


@pytest.mark.asyncio
async def test_bulk_upload_scenarios_update(client: AsyncClient):
    """Test bulk upload updates an existing scenario's fields."""
    await client.post(
        "/api/scenario/bulk",
        json={
            "scenarios": [
                {
                    "name": "BULK_UPDATE",
                    "start_datetime": "2016-01-04T00:00:00",
                    "end_datetime": "2016-12-30T00:00:00",
                    "time_interval_seconds": 86400,
                    "game_type": "ANY",
                    "initial_balance": 1000000,
                },
            ]
        }
    )

    response = await client.post(
        "/api/scenario/bulk",
        json={
            "scenarios": [
                {
                    "name": "BULK_UPDATE",
                    "start_datetime": "2016-01-04T00:00:00",
                    "end_datetime": "2016-12-30T00:00:00",
                    "time_interval_seconds": 3600,
                    "game_type": "ANY",
                    "initial_balance": 500000,
                },
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 0
    assert data["updated"] == 1

    updated = await client.get("/api/scenario/BULK_UPDATE")
    assert updated.json()["time_interval_seconds"] == 3600
    assert updated.json()["initial_balance"] == 500000


@pytest.mark.asyncio
async def test_list_scenarios_hides_eval(client: AsyncClient):
    """Scenario names containing EVAL are hidden from the listing but remain
    directly fetchable by name (so session start keeps working once announced)."""
    for name in ["EVAL_HIDDEN", "VISIBLE_X"]:
        await client.post(
            "/api/scenario/",
            json={
                "name": name,
                "start_datetime": "2016-01-04T00:00:00",
                "end_datetime": "2016-01-08T00:00:00",
                "time_interval_seconds": 86400,
                "initial_balance": 1000000,
            }
        )

    names = [s["name"] for s in (await client.get("/api/scenario/")).json()]
    assert "VISIBLE_X" in names
    assert "EVAL_HIDDEN" not in names

    response = await client.get("/api/scenario/EVAL_HIDDEN")
    assert response.status_code == 200
    assert response.json()["name"] == "EVAL_HIDDEN"


@pytest.mark.asyncio
async def test_eval_scenario_rates_forbidden(client: AsyncClient):
    """The full-rates dump is refused for evaluation scenarios (403)."""
    for name in ["EVAL_BLOCKED", "OPEN_SCENARIO"]:
        await client.post(
            "/api/scenario/",
            json={
                "name": name,
                "start_datetime": "2016-01-04T00:00:00",
                "end_datetime": "2016-01-08T00:00:00",
                "time_interval_seconds": 86400,
                "initial_balance": 1000000,
            }
        )

    response = await client.get("/api/scenario/EVAL_BLOCKED/rates")
    assert response.status_code == 403

    response = await client.get("/api/scenario/OPEN_SCENARIO/rates")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_lookup_forbidden_inside_eval_window(client: AsyncClient):
    """GET /api/rate/{ts} is refused for timestamps inside an EVAL scenario."""
    await client.post(
        "/api/scenario/",
        json={
            "name": "EVAL_WINDOW",
            "start_datetime": "2016-01-04T00:00:00",
            "end_datetime": "2016-01-06T00:00:00",
            "time_interval_seconds": 86400,
            "initial_balance": 1000000,
        }
    )
    await client.post(
        "/api/rate/bulk",
        json={"rates": [
            {"currency": "USD", "timestamp": "2016-01-05T00:00:00", "rate_to_jpy": "118.25"},
            {"currency": "USD", "timestamp": "2016-02-01T00:00:00", "rate_to_jpy": "119.00"},
        ]}
    )

    response = await client.get("/api/rate/2016-01-05T00:00:00")
    assert response.status_code == 403

    response = await client.get("/api/rate/2016-02-01T00:00:00")
    assert response.status_code == 200
