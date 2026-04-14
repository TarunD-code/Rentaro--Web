# Sprint 13 — Deploy Notes

## Overview
Deploys the new `onboarding_service` to port 8006, responsible for KYC verification and digital agreement generation.

## Required Environment Variables
Ensure the following are added to your production secrets / `.env`:
- `DOCUSIGN_INTEGRATION_KEY`
- `DOCUSIGN_SECRET`
- `SENDGRID_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`

## Database Migrations
No Alembic is set up yet (using metadata.create_all). To ensure DB tables are created:
```bash
# Activate virtual environment
source venv/Scripts/activate

# Start the service to auto-create tables
uvicorn onboarding_service.main:app --host 127.0.0.1 --port 8006
```

## Running Celery Workers
To handle async emails, signatures, and reminders:
```bash
docker-compose -f docker-compose.celery.yml up -d
```
