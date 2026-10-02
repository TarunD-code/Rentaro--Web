import pytest
import httpx
import uuid
import time
import asyncio

GATEWAY_URL = "http://127.0.0.1:8000"

@pytest.fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_featured_listing_flow():
    async with httpx.AsyncClient() as client:
        # 1. Register / Auth
        phone = f"999{str(uuid.uuid4().int)[:7]}"
        
        # We assume there is a mock OTP or dev bypass for the auth service.
        # This simulates creating a token for an owner.
        # Since auth might be mocked, we'll try to login
        res = await client.post(
            f"{GATEWAY_URL}/auth/signup", 
            json={
                "email_or_phone": phone,
                "password": "testpassword123",
                "role": "owner"
            }
        )
        assert res.status_code in [200, 201]

        res = await client.post(
            f"{GATEWAY_URL}/auth/verify-otp", 
            json={
                "email_or_phone": phone, 
                "otp": "123456"
            }
        )
        assert res.status_code == 200
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Set Profile to Owner
        res = await client.post(f"{GATEWAY_URL}/profile/me", json={"role": "owner", "first_name": "E2E", "last_name": "Test"}, headers=headers)
        # 3. Create Property
        prop_data = {
            "title": "E2E Test Mansion",
            "description": "A wonderful test home.",
            "address": "404 Automated Lane",
            "property_type": "Villa",
            "price": 15000,
            "amenities": "Pool, Gym"
        }
        res = await client.post(f"{GATEWAY_URL}/property/", json=prop_data, headers=headers)
        assert res.status_code == 200
        property_id = res.json()["id"]

        # 4. Fetch Products
        res = await client.get(f"{GATEWAY_URL}/billing/products")
        products = res.json()
        assert len(products) > 0
        gold_product = next((p for p in products if p["name"] == "Gold"), products[0])
        
        # 5. Initiate Checkout
        res = await client.post(f"{GATEWAY_URL}/billing/checkout", json={"product_id": gold_product["id"], "property_id": property_id}, headers=headers)
        assert res.status_code == 200
        purchase = res.json()
        order_id = purchase["razorpay_order_id"]

        # 6. Simulate Razorpay Webhook
        webhook_payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "order_id": order_id,
                        "id": f"pay_{uuid.uuid4().hex[:8]}"
                    }
                }
            }
        }
        res = await client.post(f"{GATEWAY_URL}/billing/webhook/razorpay", json=webhook_payload)
        assert res.status_code == 200

        # Give background tasks time to propagate HTTP events
        await asyncio.sleep(2)

        # 7. Verify Property is Featured
        res = await client.get(f"{GATEWAY_URL}/property/{property_id}")
        assert res.status_code == 200
        # Wait, the detail endpoint might not expose `is_featured`, let's check `GET /property/`
        res = await client.get(f"{GATEWAY_URL}/property/")
        props = res.json()
        target_prop = next((p for p in props if p["id"] == property_id), None)
        assert target_prop is not None

        # 8. Verify Notification
        res = await client.get(f"{GATEWAY_URL}/notifications/history", headers=headers)
        assert res.status_code == 200
        notifications = res.json()
        assert any(n["title"] == "Property Featured!" for n in notifications), "Notification not found"
