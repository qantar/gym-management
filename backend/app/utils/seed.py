"""Seed database with initial data"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.branch import Branch
from app.models.membership_plan import MembershipPlan, BillingCycle, PlanType


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Branches
        branch = Branch(name="Al Malaz Branch", code="RUH-01", city="Riyadh", address="Al Malaz District", capacity=500)
        db.add(branch)
        await db.flush()

        # Super admin
        admin = User(
            email="admin@gymos.sa", full_name="Super Admin",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.SUPER_ADMIN, branch_id=branch.id, is_active=True,
        )
        db.add(admin)

        # Plans
        plans = [
            MembershipPlan(name="Premium Annual", code="PREM-ANN", billing_cycle=BillingCycle.ANNUAL, price=2400, includes_classes=True, is_featured=True),
            MembershipPlan(name="Standard Monthly", code="STD-MON", billing_cycle=BillingCycle.MONTHLY, price=280, includes_classes=True),
            MembershipPlan(name="Basic Monthly", code="BAS-MON", billing_cycle=BillingCycle.MONTHLY, price=180, includes_classes=False),
            MembershipPlan(name="Corporate", code="CORP", billing_cycle=BillingCycle.MONTHLY, price=5000, plan_type=PlanType.CORPORATE, max_members=50),
        ]
        for p in plans:
            db.add(p)

        await db.commit()
        print("Seed complete. Login: admin@gymos.sa / Admin@123")


if __name__ == "__main__":
    asyncio.run(seed())
