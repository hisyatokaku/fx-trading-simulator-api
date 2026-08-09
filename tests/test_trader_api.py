"""Tests for Trader API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_bulk_upload_traders(client: AsyncClient):
    """Test bulk uploading traders."""
    response = await client.post(
        "/api/trader/bulk",
        json={
            "traders": [
                {"user_id": "testuser", "type": "test"},
                {"user_id": "produser", "type": "prod"},
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 2
    assert data["updated"] == 0


@pytest.mark.asyncio
async def test_bulk_upload_traders_update(client: AsyncClient):
    """Test bulk upload updates an existing trader's type."""
    await client.post(
        "/api/trader/bulk",
        json={"traders": [{"user_id": "demouser", "type": "test"}]}
    )

    response = await client.post(
        "/api/trader/bulk",
        json={"traders": [{"user_id": "demouser", "type": "prod"}]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 0
    assert data["updated"] == 1
