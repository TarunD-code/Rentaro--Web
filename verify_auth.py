import requests
import json

base_url = "http://127.0.0.1:8001/auth"

def test_login(email, password):
    print(f"Testing login for {email}...")
    try:
        response = requests.post(
            f"{base_url}/login",
            json={"email_or_phone": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Role returned = {data.get('role')}")
            return True
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_login("admin@rentora.com", "admin123")
    test_login("owner@rentora.com", "owner123")
    test_login("tenant@rentora.com", "tenant123")
