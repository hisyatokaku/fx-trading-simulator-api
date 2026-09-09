"""Tests for Rate API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_bulk_upload_rates(client: AsyncClient):
    """Test bulk uploading exchange rates."""
    response = await client.post(
        "/api/rate/bulk",
        json={
            "rates": [
                {"currency": "USD", "timestamp": "2016-01-04T00:00:00", "rate_to_jpy": "118.25"},
                {"currency": "EUR", "timestamp": "2016-01-04T00:00:00", "rate_to_jpy": "128.50"},
                {"currency": "GBP", "timestamp": "2016-01-04T00:00:00", "rate_to_jpy": "173.25"},
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 3
    assert data["updated"] == 0


@pytest.mark.asyncio
async def test_bulk_upload_rates_update(client: AsyncClient):
    """Test bulk upload updates existing rates."""
    # First upload
    await client.post(
        "/api/rate/bulk",
        json={
            "rates": [
                {"currency": "USD", "timestamp": "2016-01-05T00:00:00", "rate_to_jpy": "118.25"},
            ]
        }
    )

    # Second upload with updated rate
    response = await client.post(
        "/api/rate/bulk",
        json={
            "rates": [
                {"currency": "USD", "timestamp": "2016-01-05T00:00:00", "rate_to_jpy": "119.00"},
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 0
    assert data["updated"] == 1


@pytest.mark.asyncio
async def test_get_rates_exact(client: AsyncClient):
    """Test getting rates at exact timestamp."""
    # Upload rates
    await client.post(
        "/api/rate/bulk",
        json={
            "rates": [
                {"currency": "USD", "timestamp": "2016-01-06T00:00:00", "rate_to_jpy": "118.25"},
                {"currency": "EUR", "timestamp": "2016-01-06T00:00:00", "rate_to_jpy": "128.50"},
            ]
        }
    )

    # Get rates
    response = await client.get("/api/rate/2016-01-06T00:00:00")
    assert response.status_code == 200
    data = response.json()
    assert "USD" in data["rates"]
    assert "EUR" in data["rates"]


@pytest.mark.asyncio
async def test_get_rates_not_found(client: AsyncClient):
    """Test getting rates for non-existent timestamp."""
    response = await client.get("/api/rate/2020-01-01T00:00:00")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_rates_excludes_unsupported_currency(client: AsyncClient):
    """A stray rate row for an unsupported currency is never returned."""
    await client.post(
        "/api/rate/bulk",
        json={
            "rates": [
                {"currency": "USD", "timestamp": "2016-04-14T00:00:00", "rate_to_jpy": "109.00"},
                {"currency": "CNY", "timestamp": "2016-04-14T00:00:00", "rate_to_jpy": "16.80"},
            ]
        }
    )

    response = await client.get("/api/rate/2016-04-14T00:00:00")
    assert response.status_code == 200
    assert "USD" in response.json()["rates"]
    assert "CNY" not in response.json()["rates"]
