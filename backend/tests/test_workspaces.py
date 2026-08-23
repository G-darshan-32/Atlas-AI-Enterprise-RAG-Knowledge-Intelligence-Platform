import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_workspace(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/workspaces", json={
        "name": "Test Workspace",
        "description": "A test workspace",
    }, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Test Workspace"
    assert "id" in data
    assert "slug" in data


@pytest.mark.asyncio
async def test_list_workspaces(client: AsyncClient, auth_headers: dict):
    # Create one first
    await client.post("/api/v1/workspaces", json={"name": "WS1"}, headers=auth_headers)
    res = await client.get("/api/v1/workspaces", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1


@pytest.mark.asyncio
async def test_get_workspace(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/workspaces", json={"name": "Fetchable WS"}, headers=auth_headers)
    ws_id = create.json()["id"]
    res = await client.get(f"/api/v1/workspaces/{ws_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == ws_id


@pytest.mark.asyncio
async def test_update_workspace(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/workspaces", json={"name": "Old Name"}, headers=auth_headers)
    ws_id = create.json()["id"]
    res = await client.put(f"/api/v1/workspaces/{ws_id}", json={"name": "New Name"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_workspace(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/workspaces", json={"name": "To Delete"}, headers=auth_headers)
    ws_id = create.json()["id"]
    res = await client.delete(f"/api/v1/workspaces/{ws_id}", headers=auth_headers)
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_list_members(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/workspaces", json={"name": "Member WS"}, headers=auth_headers)
    ws_id = create.json()["id"]
    res = await client.get(f"/api/v1/workspaces/{ws_id}/members", headers=auth_headers)
    assert res.status_code == 200
    members = res.json()
    assert len(members) == 1  # creator is auto-added as admin


@pytest.mark.asyncio
async def test_workspace_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/workspaces/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert res.status_code in (403, 404)
