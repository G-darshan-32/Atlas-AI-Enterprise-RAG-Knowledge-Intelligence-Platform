import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_openapi_docs_available(client: AsyncClient):
    res = await client.get("/docs")
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_404_on_unknown_route(client: AsyncClient):
    res = await client.get("/api/v1/nonexistent")
    assert res.status_code == 404
