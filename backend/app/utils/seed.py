"""Seed database with initial data. Idempotent — safe to run multiple times."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.branch import Branch
from app.models.membership_plan import MembershipPlan, BillingCycle, PlanType
from app.models.inventory import Product, ProductCategory
from app.models.staff import Staff
from app.models.lead import Lead, LeadSource, LeadStatus


async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Tables created")

    async with AsyncSessionLocal() as db:
        # --- Branch ---
        existing_branch = (await db.execute(select(Branch).where(Branch.code == "RUH-01"))).scalar_one_or_none()
        if not existing_branch:
            branch = Branch(
                name="Al Malaz Branch", code="RUH-01", city="Riyadh",
                address="Al Malaz District, Riyadh", phone="+966-11-XXX-XXXX",
                capacity=500, opening_time="06:00", closing_time="23:00",
            )
            db.add(branch)
            await db.flush()
            branch_id = branch.id
            print(f"✓ Branch created (id={branch_id})")
        else:
            branch_id = existing_branch.id
            print(f"✓ Branch already exists (id={branch_id})")

        # --- Admin User ---
        existing_admin = (await db.execute(select(User).where(User.email == "admin@gymos.sa"))).scalar_one_or_none()
        if not existing_admin:
            admin = User(
                email="admin@gymos.sa",
                full_name="Super Admin",
                hashed_password=hash_password("Admin@123"),
                role=UserRole.SUPER_ADMIN,
                branch_id=branch_id,
                is_active=True,
            )
            db.add(admin)
            print("✓ Admin user created")
        else:
            print("✓ Admin user already exists")

        # Additional staff users
        staff_users = [
            ("manager@gymos.sa", "Omar Rashid", UserRole.BRANCH_MANAGER),
            ("trainer@gymos.sa", "Ali Hassan", UserRole.TRAINER),
            ("sales@gymos.sa", "Mohammed Salem", UserRole.SALES_REP),
            ("desk@gymos.sa", "Noor Khalid", UserRole.FRONT_DESK),
            ("accountant@gymos.sa", "Hana Al-Otaibi", UserRole.ACCOUNTANT),
        ]
        for email, name, role in staff_users:
            exists = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
            if not exists:
                db.add(User(email=email, full_name=name, hashed_password=hash_password("Staff@123"), role=role, branch_id=branch_id, is_active=True))
        print("✓ Staff users created")

        # --- Membership Plans ---
        plans_data = [
            ("Premium Annual", "PREM-ANN", BillingCycle.ANNUAL, 2400, PlanType.INDIVIDUAL, True, True),
            ("Standard Monthly", "STD-MON", BillingCycle.MONTHLY, 280, PlanType.INDIVIDUAL, True, False),
            ("Basic Monthly", "BAS-MON", BillingCycle.MONTHLY, 180, PlanType.INDIVIDUAL, False, False),
            ("Corporate Package", "CORP-MON", BillingCycle.MONTHLY, 5000, PlanType.CORPORATE, True, False),
            ("Family Pack", "FAM-QTR", BillingCycle.QUARTERLY, 1400, PlanType.FAMILY, True, False),
            ("Student Monthly", "STU-MON", BillingCycle.MONTHLY, 150, PlanType.STUDENT, True, False),
        ]
        for name, code, cycle, price, ptype, classes, featured in plans_data:
            exists = (await db.execute(select(MembershipPlan).where(MembershipPlan.code == code))).scalar_one_or_none()
            if not exists:
                db.add(MembershipPlan(
                    name=name, code=code, billing_cycle=cycle, price=price,
                    plan_type=ptype, includes_classes=classes, is_featured=featured,
                    is_active=True, tax_rate=15,
                ))
        print("✓ Membership plans created")

        # --- Products (for POS) ---
        products_data = [
            ("PRO-WHY-2KG", "Whey Protein 2kg Vanilla", ProductCategory.SUPPLEMENTS, 180, 280, 24, 10),
            ("PRE-C4-200G", "C4 Pre-workout 200g", ProductCategory.SUPPLEMENTS, 120, 195, 18, 8),
            ("PRO-BCAA-300", "BCAA 300g Berry", ProductCategory.SUPPLEMENTS, 90, 155, 15, 8),
            ("APP-TEE-BLK-M", "GymOS T-Shirt Black M", ProductCategory.APPAREL, 40, 89, 30, 10),
            ("APP-TEE-BLK-L", "GymOS T-Shirt Black L", ProductCategory.APPAREL, 40, 89, 25, 10),
            ("APP-SHO-BLU-M", "Performance Shorts Blue M", ProductCategory.APPAREL, 55, 120, 20, 8),
            ("EQP-GLP-MED", "Lifting Gloves Medium", ProductCategory.EQUIPMENT, 65, 140, 12, 5),
            ("EQP-STR-RED", "Resistance Bands Set Red", ProductCategory.EQUIPMENT, 45, 85, 18, 8),
            ("ACC-BOT-1L", "GymOS Water Bottle 1L", ProductCategory.ACCESSORIES, 25, 55, 40, 10),
            ("SUP-BAR-CHO", "Protein Bar Box Chocolate (12pc)", ProductCategory.SUPPLEMENTS, 80, 140, 20, 8),
        ]
        for sku, name, cat, cost, sell, stock, reorder in products_data:
            exists = (await db.execute(select(Product).where(Product.sku == sku))).scalar_one_or_none()
            if not exists:
                db.add(Product(
                    sku=sku, name=name, category=cat, cost_price=cost, sell_price=sell,
                    stock_quantity=stock, reorder_level=reorder, branch_id=branch_id,
                    is_active=True, tax_rate=15,
                ))
        print("✓ Products created")

        # --- Sample Leads ---
        leads_data = [
            ("Khalid Nasser", "+966501234567", LeadSource.INSTAGRAM, LeadStatus.NEW),
            ("Rania Al-Malik", "+966502345678", LeadSource.WALK_IN, LeadStatus.CONTACTED),
            ("Tariq Hassan", "+966503456789", LeadSource.REFERRAL, LeadStatus.TRIAL),
            ("Lina Mostafa", "+966504567890", LeadSource.GOOGLE, LeadStatus.PROPOSAL),
            ("Majid Al-Shehri", "+966505678901", LeadSource.WEBSITE, LeadStatus.WON),
        ]
        for name, phone, source, status in leads_data:
            exists = (await db.execute(select(Lead).where(Lead.phone == phone))).scalar_one_or_none()
            if not exists:
                db.add(Lead(full_name=name, phone=phone, source=source, status=status, branch_id=branch_id, expected_value=2400))
        print("✓ Sample leads created")

        await db.commit()

    print("\n✅ Seed complete!")
    print("   Login:    admin@gymos.sa")
    print("   Password: Admin@123")
    print("   Staff:    *@gymos.sa / Staff@123")


if __name__ == "__main__":
    asyncio.run(seed())
