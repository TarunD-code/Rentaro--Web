# Start all Rentora Services in headless mode using exact venv paths
$UVICORN = ".\venv\Scripts\uvicorn.exe"
$NPM = "npm.cmd"

echo "Starting microservices using venv..."

Start-Process -NoNewWindow -FilePath $UVICORN -ArgumentList "auth_service.main:app", "--host", "127.0.0.1", "--port", "8001"
Start-Sleep -s 1

Start-Process -NoNewWindow -FilePath $UVICORN -ArgumentList "profile_service.main:app", "--host", "127.0.0.1", "--port", "8002"
Start-Sleep -s 1

Start-Process -NoNewWindow -FilePath $UVICORN -ArgumentList "property_service.main:app", "--host", "127.0.0.1", "--port", "8003"
Start-Sleep -s 1

Start-Process -NoNewWindow -FilePath $UVICORN -ArgumentList "payment_service.main:app", "--host", "127.0.0.1", "--port", "8004"
Start-Sleep -s 1

Start-Process -NoNewWindow -FilePath $UVICORN -ArgumentList "maintenance_service.main:app", "--host", "127.0.0.1", "--port", "8005"
Start-Sleep -s 1

Start-Process -NoNewWindow -FilePath $UVICORN -ArgumentList "onboarding_service.main:app", "--host", "127.0.0.1", "--port", "8006"
Start-Sleep -s 1

# Node Service
Push-Location -Path "communication_service"
Start-Process -NoNewWindow -FilePath $NPM -ArgumentList "run", "start"
Pop-Location
Start-Sleep -s 2

# Gateway - Serving everything
Start-Process -NoNewWindow -FilePath $UVICORN -ArgumentList "gateway.main:app", "--host", "127.0.0.1", "--port", "8000"

echo "All services initiated. Access via http://127.0.0.1:8000"
