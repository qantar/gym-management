# GymOS Enterprise

Enterprise-grade gym management platform. Self-hosted, staff-only, no member portal.

## Stack
- **Frontend**: React 18 + TypeScript + Vite + TanStack Query + Recharts
- **Backend**: Python 3.13 + FastAPI + SQLAlchemy (async) + Alembic
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Containerization**: Docker Compose

## Quick Start

```bash
# 1. Clone and setup env
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Seed initial data (first run only)
docker compose exec backend python app/utils/seed.py

# 4. Access
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/api/docs
```

## Default Login
- Email: `admin@gymos.sa`
- Password: `Admin@123`

## Architecture

```
frontend (React)  →  backend (FastAPI)  →  PostgreSQL
                              ↓
                           Redis (cache)
```

## API Modules
| Module | Endpoint |
|--------|----------|
| Auth | `/api/v1/auth` |
| Members | `/api/v1/members` |
| Memberships | `/api/v1/memberships` |
| Billing | `/api/v1/invoices` |
| Attendance | `/api/v1/attendance` |
| CRM | `/api/v1/leads` |
| Inventory | `/api/v1/inventory` |
| Staff | `/api/v1/staff` |
| Schedules | `/api/v1/schedules` |
| Branches | `/api/v1/branches` |
| Reports | `/api/v1/reports` |
| Dashboard | `/api/v1/dashboard` |

## User Roles
`super_admin` · `owner` · `regional_manager` · `branch_manager` · `front_desk` · `trainer` · `accountant` · `sales_rep` · `inventory_manager` · `hr_manager`

## Project Structure
```
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # All route handlers
│   │   ├── core/               # Config, DB, security, deps
│   │   ├── models/             # SQLAlchemy models (14 modules)
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── middleware/         # Audit, rate limiting
│   │   └── utils/              # Seed, pagination
│   ├── migrations/             # Alembic migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/         # UI + Layout components
│       ├── pages/              # 10 full pages
│       ├── stores/             # Zustand (auth, ui)
│       ├── lib/                # Axios client, utils
│       └── types/              # TypeScript types
└── docker-compose.yml
```
