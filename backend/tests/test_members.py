"""Member CRUD tests."""
import pytest
from httpx import AsyncClient


MEMBER_DATA = {
    "branch_id": 1,
    "first_name": "Ahmed",
    "last_name": "Al-Rashid",
    "phone": "+966501234567",
    "email": "ahmed_test@test.com",
}


@pytest.mark.asyncio
async def test_create_member(client: AsyncClient, auth_headers: dict, seed_branch):
    data = {**MEMBER_DATA, "branch_id": seed_branch.id}
    r = await client.post("/api/v1/members/", json=data, headers=auth_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["first_name"] == "Ahmed"
    assert body["last_name"] == "Al-Rashid"
    assert body["status"] == "active"
    assert body["member_id"].startswith("M-")
    assert body["qr_code"] is not None
    return body["id"]


@pytest.mark.asyncio
async def test_list_members(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/members/", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_members_search(client: AsyncClient, auth_headers: dict, seed_branch):
    # Create member first
    await client.post("/api/v1/members/", json={**MEMBER_DATA, "branch_id": seed_branch.id, "email": "search_test@test.com", "phone": "+966501234568"}, headers=auth_headers)
    r = await client.get("/api/v1/members/?search=Ahmed", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_get_member(client: AsyncClient, auth_headers: dict, seed_branch):
    created = await client.post("/api/v1/members/", json={**MEMBER_DATA, "branch_id": seed_branch.id, "email": "get_test@test.com", "phone": "+966501234569"}, headers=auth_headers)
    mid = created.json()["id"]
    r = await client.get(f"/api/v1/members/{mid}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == mid


@pytest.mark.asyncio
async def test_get_member_not_found(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/members/99999", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_member(client: AsyncClient, auth_headers: dict, seed_branch):
    created = await client.post("/api/v1/members/", json={**MEMBER_DATA, "branch_id": seed_branch.id, "email": "update_test@test.com", "phone": "+966501234570"}, headers=auth_headers)
    mid = created.json()["id"]
    r = await client.put(f"/api/v1/members/{mid}", json={"notes": "VIP member"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["notes"] == "VIP member"


@pytest.mark.asyncio
async def test_delete_member(client: AsyncClient, auth_headers: dict, seed_branch):
    created = await client.post("/api/v1/members/", json={**MEMBER_DATA, "branch_id": seed_branch.id, "email": "delete_test@test.com", "phone": "+966501234571"}, headers=auth_headers)
    mid = created.json()["id"]
    r = await client.delete(f"/api/v1/members/{mid}", headers=auth_headers)
    assert r.status_code == 200
    # Soft deleted — should 404 on fetch
    r2 = await client.get(f"/api/v1/members/{mid}", headers=auth_headers)
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_members_requires_auth(client: AsyncClient):
    r = await client.get("/api/v1/members/")
    assert r.status_code == 401
