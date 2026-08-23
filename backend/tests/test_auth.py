import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, test_user_data: dict):
    res = await client.post("/api/v1/auth/register", json=test_user_data)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]
    assert "id" in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user_data: dict, registered_user):
    res = await client.post("/api/v1/auth/register", json=test_user_data)
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    res = await client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "weak",
        "full_name": "Weak User",
    })
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user_data: dict, registered_user):
    res = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user_data: dict, registered_user):
    res = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": "WrongPassword1",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, registered_user, auth_headers):
    res = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == registered_user["email"]


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 403  # missing bearer


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    res = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user_data: dict, registered_user):
    login_res = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    })
    refresh_token = login_res.json()["refresh_token"]

    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert "refresh_token" in res.json()

    # Old refresh token should now be invalid
    res2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res2.status_code == 401
