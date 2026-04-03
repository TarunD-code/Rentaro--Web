# Rentora — Premium Rental Platform

[![CI](https://github.com/TarunD-code/Rentaro--Web/actions/workflows/ci.yml/badge.svg)](https://github.com/TarunD-code/Rentaro--Web/actions/workflows/ci.yml)

A modern, full-stack rental marketplace built with **React + Vite** (frontend) and **FastAPI** microservices (backend).

## Architecture

```
┌────────────┐    ┌──────────────┐    ┌───────────────┐
│  React/Vite │───▶│ API Gateway  │───▶│ Auth Service  │ :8001
│   :5173    │    │   :8000      │───▶│ Profile Svc   │ :8002
└────────────┘    └──────────────┘───▶│ Property Svc  │ :8003
                                      └───────────────┘
```

## Quick Start

```bash
# Backend (requires Python 3.11+)
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
pip install fastapi uvicorn sqlalchemy pyjwt httpx python-multipart pillow

# Frontend
cd frontend
npm install
npm run dev

# Or start everything at once
start.bat
```

## Project Structure

| Directory | Description |
|---|---|
| `frontend/` | React + Vite + MUI frontend |
| `gateway/` | FastAPI API Gateway with reverse proxy |
| `auth_service/` | Authentication, JWT, OTP |
| `profile_service/` | User profiles & KYC |
| `property_service/` | Property CRUD & media pipeline |
| `scripts/` | Utility scripts |

## Key Features

- **10-Palette Theme System** — Global background switching with localStorage persistence
- **i18n** — Internationalisation support via react-i18next
- **KYC Stepper** — Multi-step identity verification flow
- **Media Pipeline** — WebP conversion + automatic resizing
- **SEO** — JSON-LD structured data via react-helmet-async
- **Landing Page** — Hero search with autocomplete + featured carousel
- **Property Detail** — Image gallery, host card, amenity grid, inquiry CTA

## CI/CD

GitHub Actions runs on every PR to `main` and `develop`:
- TypeScript compilation (`tsc -b`)
- Vite production build
- ESLint

## License

MIT
