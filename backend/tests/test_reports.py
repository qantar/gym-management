"""Reports / BI endpoint tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_membership_summary(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/reports/membership-summary", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "active" in data
    assert "expired" in data


@pytest.mark.asyncio
async def test_revenue_report(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/reports/revenue", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_revenue" in data
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_crm_report(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/reports/crm-summary", headers=auth_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_kpis(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/dashboard/kpis", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "active_members" in data
    assert "checkins_today" in data
    assert "revenue_today" in data


@pytest.mark.asyncio
async def test_pos_summary_report(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/reports/pos-summary", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_revenue" in data
    assert "transaction_count" in data


@pytest.mark.asyncio
async def test_inventory_summary_report(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/reports/inventory-summary", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "sku_count" in data
    assert "inventory_value" in data


@pytest.mark.asyncio
async def test_retention_report(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/reports/retention", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
