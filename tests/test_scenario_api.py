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
