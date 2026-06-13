"""Marketing campaign and coupon tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_campaign(client: AsyncClient, auth_headers: dict):
    r = await client.post("/api/v1/marketing/campaigns", json={
        "name": "Test SMS Campaign",
        "campaign_type": "sms",
        "target_segment": "all_members",
        "message_body": "Hi {name}, join our summer challenge!",
    }, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "draft"
    assert data["name"] == "Test SMS Campaign"


@pytest.mark.asyncio
async def test_send_campaign(client: AsyncClient, auth_headers: dict):
    created = await client.post("/api/v1/marketing/campaigns", json={
        "name": "Send Test", "campaign_type": "email",
        "target_segment": "active", "message_body": "Hello {name}",
        "subject": "Test Subject",
    }, headers=auth_headers)
    cid = created.json()["id"]
    r = await client.post(f"/api/v1/marketing/campaigns/{cid}/send", headers=auth_headers)
    assert r.status_code == 200
    assert "sent to" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_cannot_send_sent_campaign(client: AsyncClient, auth_headers: dict):
    c = await client.post("/api/v1/marketing/campaigns", json={
        "name": "Double Send", "campaign_type": "sms",
        "target_segment": "active", "message_body": "Hi",
    }, headers=auth_headers)
    cid = c.json()["id"]
    await client.post(f"/api/v1/marketing/campaigns/{cid}/send", headers=auth_headers)
    r = await client.post(f"/api/v1/marketing/campaigns/{cid}/send", headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_create_coupon(client: AsyncClient, auth_headers: dict):
    r = await client.post("/api/v1/marketing/coupons", json={
        "code": "TESTCOUPON20", "discount_type": "percentage",
        "discount_value": "20.00", "min_purchase": "100.00",
    }, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["code"] == "TESTCOUPON20"


@pytest.mark.asyncio
async def test_duplicate_coupon_rejected(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/marketing/coupons", json={
        "code": "DUPCODE", "discount_type": "fixed", "discount_value": "50.00",
    }, headers=auth_headers)
    r = await client.post("/api/v1/marketing/coupons", json={
        "code": "DUPCODE", "discount_type": "fixed", "discount_value": "50.00",
    }, headers=auth_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_validate_coupon(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/marketing/coupons", json={
        "code": "VALID10", "discount_type": "percentage", "discount_value": "10.00",
        "min_purchase": "0.00",
    }, headers=auth_headers)
    r = await client.post("/api/v1/marketing/coupons/validate?code=VALID10&amount=500", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is True
    assert float(data["discount_amount"]) == pytest.approx(50.0, rel=0.01)


@pytest.mark.asyncio
async def test_segment_count(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/marketing/segments/count?segment=all_members", headers=auth_headers)
    assert r.status_code == 200
    assert "count" in r.json()
