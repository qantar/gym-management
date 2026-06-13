from fastapi import APIRouter
from app.api.v1.endpoints import (
    pos,
    auth, users, members, memberships, invoices,
    attendance, leads, staff, inventory, schedules,
    branches, reports, dashboard
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(members.router, prefix="/members", tags=["Members"])
api_router.include_router(memberships.router, prefix="/memberships", tags=["Memberships"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Billing"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(leads.router, prefix="/leads", tags=["CRM"])
api_router.include_router(staff.router, prefix="/staff", tags=["Staff"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["Scheduling"])
api_router.include_router(branches.router, prefix="/branches", tags=["Branches"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(pos.router, prefix="/pos", tags=["POS"])
