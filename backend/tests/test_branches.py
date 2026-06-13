"""Branch management tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_branches(client: AsyncClient, auth_headers: dict, seed_branch):
    r = await client.get("/api/v1/branches/", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_branch(client: AsyncClient, auth_headers: dict):
    r = await client.post("/api/v1/branches/", json={
        "name": "New Test Branch", "code": "NTB-01",
        "city": "Jeddah", "capacity": 300,
    }, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["code"] == "NTB-01"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_duplicate_code_rejected(client: AsyncClient, auth_headers: dict, seed_branch):
    r = await client.post("/api/v1/branches/", json={
        "name": "Dup Branch", "code": seed_branch.code,
        "city": "Riyadh", "capacity": 100,
    }, headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_branch_stats(client: AsyncClient, auth_headers: dict, seed_branch):
    r = await client.get(f"/api/v1/branches/{seed_branch.id}/stats", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "active_members" in data
    assert "revenue_month" in data
    assert "checkins_today" in data


@pytest.mark.asyncio
async def test_update_branch(client: AsyncClient, auth_headers: dict):
    b = await client.post("/api/v1/branches/", json={"name": "Update Me", "code": "UPD-01", "city": "Riyadh", "capacity": 200}, headers=auth_headers)
    bid = b.json()["id"]
    r = await client.put(f"/api/v1/branches/{bid}", json={"city": "Dammam"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["city"] == "Dammam"
