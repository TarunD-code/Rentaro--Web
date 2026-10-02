import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from property_service.main import app

client = TestClient(app)

print("--- Testing GET /properties ---")
resp = client.get("/properties")
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Count returned: {len(data)}")
    if data:
        print(f"First item title: {data[0].get('title')}")
else:
    print(f"Error: {resp.text}")

print("\n--- Testing GET /search ---")
resp = client.get("/search")
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    # It might return a paginated response or list
    if isinstance(data, dict) and "items" in data:
        print(f"Count returned: {len(data['items'])}")
    else:
        print(f"Count returned: {len(data)}")
else:
    print(f"Error: {resp.text}")
    
print("\n--- Testing GET /map ---")
resp = client.get("/map")
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Count returned: {len(data)}")
else:
    print(f"Error: {resp.text}")
