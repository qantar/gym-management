"""POS / sales tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_sale(client: AsyncClient, auth_headers: dict, seed_branch):
    # Create product
    p = await client.post("/api/v1/inventory/products", json={
        "sku": "POS-TST-001", "name": "POS Test Item", "category": "accessories",
        "cost_price": "20.00", "sell_price": "50.00", "stock_quantity": 100, "reorder_level": 5,
    }, headers=auth_headers)
    pid = p.json()["id"]

    r = await client.post("/api/v1/pos/sales", json={
        "branch_id": seed_branch.id,
        "payment_method": "cash",
        "discount_amount": "0.00",
        "tax_rate": "15",
        "items": [{"product_id": pid, "quantity": 2, "unit_price": "50.00", "discount": "0.00"}],
    }, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["sale_number"].startswith("POS-")
    assert float(data["subtotal"]) == pytest.approx(100.0)
    assert float(data["tax_amount"]) == pytest.approx(15.0)
    assert float(data["total"]) == pytest.approx(115.0)
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_sale_deducts_stock(client: AsyncClient, auth_headers: dict, seed_branch):
    p = await client.post("/api/v1/inventory/products", json={
        "sku": "POS-TST-002", "name": "Stock Deduct Test", "category": "accessories",
        "cost_price": "10.00", "sell_price": "20.00", "stock_quantity": 10, "reorder_level": 2,
    }, headers=auth_headers)
    pid = p.json()["id"]

    await client.post("/api/v1/pos/sales", json={
        "branch_id": seed_branch.id, "payment_method": "card", "discount_amount": "0.00", "tax_rate": "15",
        "items": [{"product_id": pid, "quantity": 3, "unit_price": "20.00", "discount": "0.00"}],
    }, headers=auth_headers)

    prod = await client.get(f"/api/v1/inventory/products/{pid}", headers=auth_headers)
    assert prod.json()["stock_quantity"] == 7


@pytest.mark.asyncio
async def test_sale_insufficient_stock(client: AsyncClient, auth_headers: dict, seed_branch):
    p = await client.post("/api/v1/inventory/products", json={
        "sku": "POS-TST-003", "name": "Low Stock", "category": "accessories",
        "cost_price": "10.00", "sell_price": "20.00", "stock_quantity": 2, "reorder_level": 1,
    }, headers=auth_headers)
    pid = p.json()["id"]
    r = await client.post("/api/v1/pos/sales", json={
        "branch_id": seed_branch.id, "payment_method": "cash", "discount_amount": "0.00", "tax_rate": "15",
        "items": [{"product_id": pid, "quantity": 100, "unit_price": "20.00", "discount": "0.00"}],
    }, headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_void_sale(client: AsyncClient, auth_headers: dict, seed_branch):
    p = await client.post("/api/v1/inventory/products", json={
        "sku": "POS-TST-004", "name": "Void Test", "category": "accessories",
        "cost_price": "10.00", "sell_price": "20.00", "stock_quantity": 50, "reorder_level": 5,
    }, headers=auth_headers)
    pid = p.json()["id"]
    sale = await client.post("/api/v1/pos/sales", json={
        "branch_id": seed_branch.id, "payment_method": "cash", "discount_amount": "0.00", "tax_rate": "15",
        "items": [{"product_id": pid, "quantity": 1, "unit_price": "20.00", "discount": "0.00"}],
    }, headers=auth_headers)
    sale_id = sale.json()["id"]
    r = await client.post(f"/api/v1/pos/sales/{sale_id}/void", headers=auth_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_pos_summary(client: AsyncClient, auth_headers: dict, seed_branch):
    r = await client.get(f"/api/v1/pos/sales/summary?branch_id={seed_branch.id}", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "today_revenue" in data
    assert "today_transactions" in data
