import time
import sys
import httpx
import json

GATEWAY_URL = "http://localhost:8000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def check_gateway_diagnostics():
    print_header("1. API Gateway Diagnostics Verification")
    try:
        response = httpx.get(f"{GATEWAY_URL}/diagnostics", timeout=10.0)
        if response.status_code != 200:
            print(f"❌ Gateway returned status {response.status_code}")
            return False, 0
            
        data = response.json()
        print(f"Gateway Overall Status: {data.get('status').upper()}")
        
        # Check Infra
        infra = data.get("infrastructure", {})
        infra_score = 0
        total_infra = 4
        print("\n--- Core Infrastructure ---")
        for key in ["postgres", "redis", "rabbitmq"]:
            status = infra.get(key, "unknown")
            if "online" in status.lower():
                print(f"✅ {key.capitalize()}: Online")
                infra_score += 1
            else:
                print(f"❌ {key.capitalize()}: {status}")
                
        storage_status = infra.get("storage", {}).get("status", "unknown")
        if "online" in storage_status.lower():
            print(f"✅ Storage: Online")
            infra_score += 1
        else:
            print(f"❌ Storage: {storage_status}")
            
        # Check Services
        services = data.get("services", {})
        total_services = 15
        service_score = 0
        
        print("\n--- Microservices ---")
        for service, details in services.items():
            status = details.get("status", "unknown")
            if status == "online":
                print(f"✅ {service}: Online")
                service_score += 1
            else:
                print(f"❌ {service}: {status} - {details.get('error', '')}")
                
        points = (infra_score / total_infra) * 30 + (service_score / total_services) * 50
        return True, points
    except Exception as e:
        print(f"❌ Failed to reach Gateway: {e}")
        return False, 0

def check_search_endpoints():
    print_header("2. Search Intelligence Verification")
    search_score = 0
    total_endpoints = 2
    
    # Test Autocomplete
    try:
        response = httpx.get(f"{GATEWAY_URL}/search/autocomplete?q=apt", timeout=5.0)
        if response.status_code == 200:
            print("✅ /search/autocomplete: 200 OK")
            search_score += 1
        else:
            print(f"❌ /search/autocomplete: {response.status_code}")
    except Exception as e:
        print(f"❌ /search/autocomplete: Failed ({e})")
        
    # Test Properties
    try:
        payload = {"q": "apartment", "page": 1, "page_size": 10}
        response = httpx.post(f"{GATEWAY_URL}/search/properties", json=payload, timeout=5.0)
        if response.status_code == 200:
            print("✅ /search/properties: 200 OK")
            search_score += 1
        else:
            print(f"❌ /search/properties: {response.status_code}")
    except Exception as e:
        print(f"❌ /search/properties: Failed ({e})")
        
    points = (search_score / total_endpoints) * 20
    return True, points

def run_validation():
    print("Starting Platform Stabilization & Runtime Recovery Validation...")
    print("Waiting 5 seconds for services to settle...")
    time.sleep(5)
    
    total_score = 0
    success, infra_points = check_gateway_diagnostics()
    total_score += infra_points
    
    success, search_points = check_search_endpoints()
    total_score += search_points
    
    print_header("FINAL READINESS REPORT")
    print(f"Production Readiness Score: {total_score:.1f}%")
    
    if total_score >= 90:
        print("✅ PLATFORM IS FULLY OPERATIONAL AND PRODUCTION READY.")
        sys.exit(0)
    else:
        print("❌ PLATFORM DEGRADED. Check logs for offline services.")
        sys.exit(1)

if __name__ == "__main__":
    run_validation()
