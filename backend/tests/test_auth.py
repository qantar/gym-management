"""Auth endpoint tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, seed_admin):
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": "test_admin@gymos.sa", "password": "Admin@123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, seed_admin):
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": "test_admin@gymos.sa", "password": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient):
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@gymos.sa", "password": "Admin@123"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/users/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "test_admin@gymos.sa"
    assert data["role"] == "super_admin"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    r = await client.get("/api/v1/users/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, seed_admin):
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "test_admin@gymos.sa", "password": "Admin@123"},
    )
    refresh_token = login.json()["refresh_token"]
    r = await client.post(f"/api/v1/auth/refresh?refresh_token={refresh_token}")
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_headers: dict):
    r = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert r.status_code == 200
