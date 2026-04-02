import httpx
import asyncio
import json

async def test_admin_login():
    url = "http://127.0.0.1:8000/auth/login"
    payload = {
        "email_or_phone": "admin@rentora.com",
        "password": "testing123",
        "role": "admin"
    }
    
    print(f"Testing login at {url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and data.get("role") == "admin":
                    print("✅ Admin login successful!")
                else:
                    print("❌ Login succeeded but response data is incorrect.")
            else:
                print(f"❌ Login failed with status {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error during request: {e}")

if __name__ == "__main__":
    asyncio.run(test_admin_login())
