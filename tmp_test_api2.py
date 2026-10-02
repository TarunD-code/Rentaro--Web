import sys
import os
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        print("--- Testing GET /property ---")
        try:
            resp = await client.get("/property")
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"Count returned: {len(data)}")
            else:
                print(f"Error: {resp.text}")
        except Exception as e:
            print(e)
            
        print("\n--- Testing GET /property/search ---")
        try:
            resp = await client.get("/property?q=Mumbai")
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"Count returned: {len(data)}")
            else:
                print(f"Error: {resp.text}")
        except Exception as e:
            print(e)

if __name__ == "__main__":
    asyncio.run(test_api())
