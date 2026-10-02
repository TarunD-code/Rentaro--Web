import sys
import os
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        print("--- Testing POST /search/properties ---")
        try:
            payload = {
                "min_price": 0,
                "max_price": 200000,
                "ranking_profile": "default",
                "page": 1,
                "page_size": 50
            }
            resp = await client.post("/search/properties", json=payload)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"Total returned: {data.get('total')}")
                if data.get('results'):
                    first = data['results'][0]
                    print(f"Keys: {list(first.keys())}")
                    print(f"First item title: {first.get('title')}")
                    print(f"Amenities: {first.get('amenities')}")
                    print(f"Images: {first.get('images')}")
                    print(f"Locality: {first.get('locality')}")
            else:
                print(f"Error: {resp.text}")
        except Exception as e:
            print(e)

if __name__ == "__main__":
    asyncio.run(test_api())
