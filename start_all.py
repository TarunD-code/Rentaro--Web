import subprocess
import time
import os

services = [
    ("API Gateway", "uvicorn gateway.main:app --host 127.0.0.1 --port 8000"),
    ("Auth Service", "uvicorn auth_service.main:app --host 127.0.0.1 --port 8001"),
    ("Profile Service", "uvicorn profile_service.main:app --host 127.0.0.1 --port 8002"),
    ("Property Service", "uvicorn property_service.main:app --host 127.0.0.1 --port 8003"),
    ("Payment Service", "uvicorn payment_service.main:app --host 127.0.0.1 --port 8004"),
    ("Maintenance Service", "uvicorn maintenance_service.main:app --host 127.0.0.1 --port 8005"),
    ("Onboarding Service", "uvicorn onboarding_service.main:app --host 127.0.0.1 --port 8006"),
    ("Communication Service", "cd communication_service && npm run start"),
    ("Agreements Service", "uvicorn agreements_service.main:app --host 127.0.0.1 --port 8008"),
    ("Billing Service", "uvicorn billing_service.main:app --host 127.0.0.1 --port 8009"),
    ("Owner Dashboard", "uvicorn owner_dashboard_service.main:app --host 127.0.0.1 --port 8010"),
    ("Subscription Service", "uvicorn subscription_service.main:app --host 127.0.0.1 --port 8011"),
    ("Support Service", "uvicorn support_service.main:app --host 127.0.0.1 --port 8012"),
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
