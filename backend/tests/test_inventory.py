"""Inventory tests."""
import pytest
from httpx import AsyncClient


PRODUCT = {
    "sku": "TEST-PRO-001",
    "name": "Test Protein 1kg",
    "category": "supplements",
    "cost_price": "100.00",
    "sell_price": "180.00",
    "stock_quantity": 50,
    "reorder_level": 10,
}


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, auth_headers: dict):
    r = await client.post("/api/v1/inventory/products", json=PRODUCT, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["sku"] == "TEST-PRO-001"
    assert data["stock_quantity"] == 50


@pytest.mark.asyncio
async def test_duplicate_sku_rejected(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/inventory/products", json={**PRODUCT, "sku": "DUP-SKU-001"}, headers=auth_headers)
    r = await client.post("/api/v1/inventory/products", json={**PRODUCT, "sku": "DUP-SKU-001"}, headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/inventory/products", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.asyncio
async def test_stock_adjust_in(client: AsyncClient, auth_headers: dict, seed_branch):
    p = await client.post("/api/v1/inventory/products", json={**PRODUCT, "sku": "ADJ-001"}, headers=auth_headers)
    pid = p.json()["id"]
    r = await client.post("/api/v1/inventory/adjust", json={
        "product_id": pid, "branch_id": seed_branch.id,
        "quantity": 20, "movement_type": "in", "notes": "Restock",
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["new_quantity"] == 70


@pytest.mark.asyncio
async def test_stock_adjust_out(client: AsyncClient, auth_headers: dict, seed_branch):
    p = await client.post("/api/v1/inventory/products", json={**PRODUCT, "sku": "ADJ-002"}, headers=auth_headers)
    pid = p.json()["id"]
    r = await client.post("/api/v1/inventory/adjust", json={
        "product_id": pid, "branch_id": seed_branch.id,
        "quantity": 10, "movement_type": "out",
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["new_quantity"] == 40


@pytest.mark.asyncio
async def test_insufficient_stock_rejected(client: AsyncClient, auth_headers: dict, seed_branch):
    p = await client.post("/api/v1/inventory/products", json={**PRODUCT, "sku": "ADJ-003"}, headers=auth_headers)
    pid = p.json()["id"]
    r = await client.post("/api/v1/inventory/adjust", json={
        "product_id": pid, "branch_id": seed_branch.id,
        "quantity": 9999, "movement_type": "out",
    }, headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_low_stock_alerts(client: AsyncClient, auth_headers: dict, seed_branch):
    # Create a product with low stock
    await client.post("/api/v1/inventory/products", json={**PRODUCT, "sku": "LOW-001", "stock_quantity": 3, "reorder_level": 10}, headers=auth_headers)
    r = await client.get("/api/v1/inventory/alerts/low-stock", headers=auth_headers)
    assert r.status_code == 200
    alerts = r.json()
    assert isinstance(alerts, list)
    low_skus = [a["sku"] for a in alerts]
    assert "LOW-001" in low_skus


@pytest.mark.asyncio
async def test_inventory_valuation(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/inventory/valuation", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "sku_count" in data
    assert "cost_value" in data
    assert "sell_value" in data
