"""CRM / leads tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_lead(client: AsyncClient, auth_headers: dict, seed_branch):
    r = await client.post("/api/v1/leads/", json={
        "branch_id": seed_branch.id,
        "full_name": "Khalid Test",
        "phone": "+966501299001",
        "source": "instagram",
        "status": "new",
        "expected_value": "2400.00",
    }, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "new"
    assert data["full_name"] == "Khalid Test"


@pytest.mark.asyncio
async def test_advance_lead(client: AsyncClient, auth_headers: dict, seed_branch):
    created = await client.post("/api/v1/leads/", json={
        "branch_id": seed_branch.id, "full_name": "Advance Test",
        "phone": "+966501299002", "source": "walk_in",
    }, headers=auth_headers)
    lead_id = created.json()["id"]

    r = await client.put(f"/api/v1/leads/{lead_id}", json={"status": "contacted"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "contacted"


@pytest.mark.asyncio
async def test_win_lead_sets_converted_at(client: AsyncClient, auth_headers: dict, seed_branch):
    created = await client.post("/api/v1/leads/", json={
        "branch_id": seed_branch.id, "full_name": "Win Test",
        "phone": "+966501299003", "source": "referral",
    }, headers=auth_headers)
    lead_id = created.json()["id"]
    r = await client.put(f"/api/v1/leads/{lead_id}", json={"status": "won"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "won"


@pytest.mark.asyncio
async def test_list_leads_by_status(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/leads/?status=new", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert all(item["status"] == "new" for item in data["items"])


@pytest.mark.asyncio
async def test_crm_summary_report(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/reports/crm-summary", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    for stage in ["new", "contacted", "trial", "proposal", "won", "lost"]:
        assert stage in data
    assert "conversion_rate" in data
