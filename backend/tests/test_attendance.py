"""Attendance and check-in tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_checkin_manual(client: AsyncClient, auth_headers: dict, seed_branch):
    # Create member
    m = await client.post("/api/v1/members/", json={
        "branch_id": seed_branch.id, "first_name": "Attend",
        "last_name": "Test", "phone": "+966501290001",
    }, headers=auth_headers)
    member_id = m.json()["id"]

    r = await client.post("/api/v1/attendance/checkin", json={
        "member_id": member_id, "branch_id": seed_branch.id, "method": "manual",
    }, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["member_id"] == member_id
    assert data["check_out"] is None
    return data["id"]


@pytest.mark.asyncio
async def test_duplicate_checkin_rejected(client: AsyncClient, auth_headers: dict, seed_branch):
    m = await client.post("/api/v1/members/", json={
        "branch_id": seed_branch.id, "first_name": "Dup", "last_name": "Check",
        "phone": "+966501290002",
    }, headers=auth_headers)
    member_id = m.json()["id"]
    await client.post("/api/v1/attendance/checkin", json={"member_id": member_id, "branch_id": seed_branch.id, "method": "manual"}, headers=auth_headers)
    r = await client.post("/api/v1/attendance/checkin", json={"member_id": member_id, "branch_id": seed_branch.id, "method": "manual"}, headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_checkout(client: AsyncClient, auth_headers: dict, seed_branch):
    m = await client.post("/api/v1/members/", json={
        "branch_id": seed_branch.id, "first_name": "Check", "last_name": "Out",
        "phone": "+966501290003",
    }, headers=auth_headers)
    checkin = await client.post("/api/v1/attendance/checkin", json={
        "member_id": m.json()["id"], "branch_id": seed_branch.id, "method": "manual",
    }, headers=auth_headers)
    log_id = checkin.json()["id"]
    r = await client.post(f"/api/v1/attendance/checkout/{log_id}", headers=auth_headers)
    assert r.status_code == 200
    assert "duration_minutes" in r.json()


@pytest.mark.asyncio
async def test_today_stats(client: AsyncClient, auth_headers: dict, seed_branch):
    r = await client.get(f"/api/v1/attendance/live/{seed_branch.id}", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_today" in data
    assert "in_gym_now" in data


@pytest.mark.asyncio
async def test_checkin_by_qr(client: AsyncClient, auth_headers: dict, seed_branch):
    m = await client.post("/api/v1/members/", json={
        "branch_id": seed_branch.id, "first_name": "QR", "last_name": "User",
        "phone": "+966501290004",
    }, headers=auth_headers)
    qr = m.json()["qr_code"]
    assert qr is not None
    r = await client.post("/api/v1/attendance/checkin", json={
        "qr_code": qr, "branch_id": seed_branch.id, "method": "qr",
    }, headers=auth_headers)
    assert r.status_code == 200
