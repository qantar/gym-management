# GymOS Enterprise

> Enterprise-grade gym management platform. Self-hosted. Staff-only. No member portal.

[![CI](https://github.com/qantar/gym-management/actions/workflows/ci.yml/badge.svg)](https://github.com/qantar/gym-management/actions)

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + TanStack Query + Recharts |
| Backend | Python 3.13 + FastAPI + SQLAlchemy (async) + Pydantic v2 |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Realtime | WebSockets (native FastAPI) |
| Desktop | Electron 31 |
| Container | Docker Compose |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/qantar/gym-management.git
cd gym-management

# 2. Start (Docker)
make up

# 3. Seed initial data (first run only)
make seed

# 4. Open
# Frontend:  http://localhost:5173
# API docs:  http://localhost:8000/api/docs
```

**Default credentials:**
- Admin: `admin@gymos.sa` / `Admin@123`
- Staff: `*@gymos.sa` / `Staff@123`

## Modules (16 pages)

| Module | Route | Description |
|--------|-------|-------------|
| Dashboard | `/dashboard` | Live KPIs, revenue chart, expiry alerts, inventory alerts |
| Members | `/members` | Member CRUD, search, freeze, QR codes |
| Billing | `/billing` | Invoices, payments, collections, VAT |
| POS | `/pos` | Barcode scan, cart, checkout, receipt print |
| Attendance | `/attendance` | QR/RFID/PIN/Manual check-in + live WebSocket feed |
| Scheduling | `/scheduling` | Week/Day/List calendar, class booking, waitlist |
| CRM | `/crm` | Kanban pipeline, drag-drop, lead scoring |
| Inventory | `/inventory` | Stock management, POs, low-stock alerts |
| Staff | `/staff` | Employee profiles, KPI tracking, attendance |
| Payroll | `/payroll` | Run payroll, per-slip editing, approve/pay workflow |
| Marketing | `/marketing` | SMS/Email/WhatsApp campaigns, coupons |
| Reports | `/reports` | Revenue, retention, churn, CRM, inventory charts |
| Branches | `/branches` | Multi-branch management, live per-branch stats |
| Audit Log | `/audit` | Full audit trail with filters |
| Settings | `/settings` | RBAC, notifications, security, general |

## API Reference

17 endpoint groups — full OpenAPI docs at `/api/docs` when running.

```
/api/v1/auth          Login, refresh, logout
/api/v1/users         User CRUD + me
/api/v1/members       Member CRUD + search
/api/v1/memberships   Plans, freeze, unfreeze
/api/v1/invoices      Billing, payments, collections
/api/v1/attendance    Check-in, checkout, WS feed
/api/v1/leads         CRM pipeline
/api/v1/staff         Employee management + attendance
/api/v1/inventory     Products, stock, purchase orders
/api/v1/schedules     Classes, booking, waitlist
/api/v1/branches      Branch CRUD + live stats
/api/v1/pos           Sales, void, receipt
/api/v1/marketing     Campaigns, coupons, segments
/api/v1/payroll       Runs, slips, approve, pay
/api/v1/reports       BI queries (revenue, retention, CRM...)
/api/v1/dashboard     Aggregated KPIs
/api/v1/audit         Audit log
```

## User Roles

`super_admin` · `owner` · `regional_manager` · `branch_manager` · `front_desk` · `trainer` · `accountant` · `sales_rep` · `inventory_manager` · `hr_manager`

## Development

```bash
make test          # Run 60+ backend tests
make lint          # Ruff lint check
make migrate       # Alembic DB migrations
make logs          # Tail service logs
make dev-backend   # Hot-reload backend (no Docker)
make dev-frontend  # Vite dev server (no Docker)
```

## Database

- 27 tables, fully normalized
- Soft deletes (`is_deleted` flag)
- Audit trail on all entities
- Alembic versioned migrations
- Composite + trigram indexes for performance

## Desktop (Electron)

```bash
cd electron
npm install
npm run dev          # Dev mode (connects to local services)
npm run build:win    # Windows NSIS installer
npm run build:mac    # macOS DMG
npm run build:linux  # Linux AppImage
```

## Architecture

```
Electron Shell
     │
     ▼
React SPA (Vite)
     │  (HTTP + WebSocket)
     ▼
FastAPI (Python 3.13)
     │
     ├── PostgreSQL 16  (primary store)
     ├── Redis 7        (cache + sessions)
     └── WebSockets     (live attendance feed)
```

## Environment Variables

Copy `.env.example` to `.env` and update:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | `gymos_secret_change_me` | **Change in production** |
| `REDIS_PASSWORD` | `redis_secret_change_me` | **Change in production** |
| `SECRET_KEY` | dev key | **Generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`** |
| `ENVIRONMENT` | `development` | Set to `production` for prod |

## License

Proprietary — GymOS Enterprise. All rights reserved.
