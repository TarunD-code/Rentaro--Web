import subprocess
import time
import os
import sys

# --- ENVIRONMENT & PRE-FLIGHT CHECKS ---
print("Validating Environment...")
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# Check for rogue shadow .env files
for root, dirs, files in os.walk(os.path.dirname(__file__)):
    if ".env" in files and root != os.path.dirname(__file__):
        if "venv" not in root and "node_modules" not in root and ".git" not in root:
            print(f"[WARNING] Shadow .env file found at {os.path.join(root, '.env')}. This might override global credentials.")

# Database Validation
try:
    import psycopg2
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("[FATAL] DATABASE_URL is not set in .env")
        sys.exit(1)
    
    print("[INFO] Testing PostgreSQL connection...")
    conn = psycopg2.connect(db_url)
    conn.close()
    print("[SUCCESS] PostgreSQL Authentication Successful.")
except psycopg2.OperationalError as e:
    print("\n[FATAL] PostgreSQL Database Authentication Failed.")
    print("This indicates your .env password does not match the database engine.")
    print("Aborting startup to prevent cascade tracebacks.")
    sys.exit(1)
except ImportError:
    print("[WARNING] psycopg2 not installed, skipping DB pre-flight check.")
except Exception as e:
    print(f"[WARNING] Could not validate DB connection prior to startup: {e}")

# --- STARTUP LOGIC ---

services = [
    ("API Gateway", "uvicorn gateway.main:app --host 0.0.0.0 --port 8000"),
    ("Auth Service", "uvicorn auth_service.main:app --host 0.0.0.0 --port 8001"),
    ("Profile Service", "uvicorn profile_service.main:app --host 0.0.0.0 --port 8002"),
    ("Property Service", "uvicorn property_service.main:app --host 0.0.0.0 --port 8003"),
    ("Payment Service", "uvicorn payment_service.main:app --host 0.0.0.0 --port 8004"),
    ("Maintenance Service", "uvicorn maintenance_service.main:app --host 0.0.0.0 --port 8005"),
    ("Onboarding Service", "uvicorn onboarding_service.main:app --host 0.0.0.0 --port 8006"),
    ("Communication Service", "cd communication_service && npm run start"),
    ("Agreements Service", "uvicorn agreements_service.main:app --host 0.0.0.0 --port 8008"),
    ("Billing Service", "uvicorn billing_service.main:app --host 0.0.0.0 --port 8009"),
    ("Owner Dashboard", "uvicorn owner_dashboard_service.main:app --host 0.0.0.0 --port 8010"),
    ("Subscription Service", "uvicorn subscription_service.main:app --host 0.0.0.0 --port 8011"),
    ("Support Service", "uvicorn support_service.main:app --host 0.0.0.0 --port 8012"),
    ("Notification Service", "uvicorn notification_service.main:app --host 0.0.0.0 --port 8013"),
    ("Geo Amenity Service", "uvicorn geo_amenity_service.main:app --host 0.0.0.0 --port 8014"),
    ("Search Service", "uvicorn search_service.main:app --host 0.0.0.0 --port 8015"),
    ("KYC Service", "uvicorn kyc_service.main:app --host 0.0.0.0 --port 8016"),
    ("Frontend", "cd frontend && npm run dev")
]

processes = []

print("Starting Rentora Microservices Ensemble...")

# Use the virtual environment python for backend services
venv_python = os.path.join("venv", "Scripts", "python.exe")

for name, cmd in services:
    print(f"Launching {name}...")
    if "uvicorn" in cmd:
        full_cmd = f"{venv_python} -m {cmd}"
    else:
        full_cmd = cmd
    
    p = subprocess.Popen(full_cmd, shell=True)
    processes.append((name, p))
    time.sleep(1) # Brief pause to avoid CPU spike

print("\n[START] All services are initializing in the background.")
print("Antigravity is monitoring the orchestration.")

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("Shutting down services...")
    for name, p in processes:
        p.terminate()
