"""Invoice and payment tests."""
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient


def future_date():
    return (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()


@pytest.mark.asyncio
async def test_create_invoice(client: AsyncClient, auth_headers: dict, seed_branch):
    # Need a member first
    m = await client.post("/api/v1/members/", json={
        "branch_id": seed_branch.id, "first_name": "Invoice", "last_name": "Test",
        "phone": "+966501230001", "email": "inv_test@test.com",
    }, headers=auth_headers)
    member_id = m.json()["id"]

    r = await client.post("/api/v1/invoices/", json={
        "member_id": member_id, "branch_id": seed_branch.id,
        "description": "Premium Annual Membership",
        "subtotal": "2400.00", "discount_amount": "0.00",
        "tax_rate": "15.00", "due_date": future_date(),
    }, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["invoice_number"].startswith("INV-")
    assert data["status"] == "pending"
    assert float(data["total"]) == pytest.approx(2760.0, rel=0.01)
    return data["id"]


@pytest.mark.asyncio
async def test_list_invoices(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/invoices/", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.asyncio
async def test_record_payment(client: AsyncClient, auth_headers: dict, seed_branch):
    m = await client.post("/api/v1/members/", json={
        "branch_id": seed_branch.id, "first_name": "Pay", "last_name": "Test",
        "phone": "+966501230002", "email": "pay_test@test.com",
    }, headers=auth_headers)
    member_id = m.json()["id"]

    inv = await client.post("/api/v1/invoices/", json={
        "member_id": member_id, "branch_id": seed_branch.id,
        "description": "Test", "subtotal": "1000.00",
        "discount_amount": "0.00", "tax_rate": "15.00", "due_date": future_date(),
    }, headers=auth_headers)
    inv_id = inv.json()["id"]
    total = float(inv.json()["total"])

    r = await client.post(f"/api/v1/invoices/{inv_id}/pay", json={
        "invoice_id": inv_id, "amount": str(total), "method": "cash",
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_overpayment_rejected(client: AsyncClient, auth_headers: dict, seed_branch):
    m = await client.post("/api/v1/members/", json={
        "branch_id": seed_branch.id, "first_name": "Over", "last_name": "Pay",
        "phone": "+966501230003", "email": "overpay@test.com",
    }, headers=auth_headers)
    inv = await client.post("/api/v1/invoices/", json={
        "member_id": m.json()["id"], "branch_id": seed_branch.id,
        "description": "Test", "subtotal": "500.00",
        "discount_amount": "0.00", "tax_rate": "15.00", "due_date": future_date(),
    }, headers=auth_headers)
    inv_id = inv.json()["id"]
    r = await client.post(f"/api/v1/invoices/{inv_id}/pay", json={
        "invoice_id": inv_id, "amount": "99999.00", "method": "cash",
    }, headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_overdue_summary(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/invoices/summary/overdue", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "overdue_count" in data
    assert "overdue_total" in data
