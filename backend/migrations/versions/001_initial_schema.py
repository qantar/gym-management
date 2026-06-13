"""Initial schema — all GymOS tables

Revision ID: 001_initial
Revises:
Create Date: 2026-06-13 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # users
    op.create_table("users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("phone", sa.String(20), unique=True, nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, default="front_desk"),
        sa.Column("branch_id", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_mfa_enabled", sa.Boolean, default=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_login_attempts", sa.Integer, default=0),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # branches
    op.create_table("branches",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("manager_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("capacity", sa.Integer, default=500),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("opening_time", sa.String(5), default="06:00"),
        sa.Column("closing_time", sa.String(5), default="23:00"),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # membership_plans
    op.create_table("membership_plans",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("plan_type", sa.String(20), default="individual"),
        sa.Column("billing_cycle", sa.String(20), default="monthly"),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("setup_fee", sa.Numeric(10, 2), default=0),
        sa.Column("max_members", sa.Integer, default=1),
        sa.Column("max_freezes_per_year", sa.Integer, default=2),
        sa.Column("max_freeze_days", sa.Integer, default=30),
        sa.Column("allows_guest", sa.Boolean, default=False),
        sa.Column("guest_passes_per_month", sa.Integer, default=0),
        sa.Column("includes_classes", sa.Boolean, default=True),
        sa.Column("classes_per_month", sa.Integer, nullable=True),
        sa.Column("capacity", sa.Integer, nullable=True),
        sa.Column("current_subscribers", sa.Integer, default=0),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_featured", sa.Boolean, default=False),
        sa.Column("features", sa.Text, nullable=True),
        sa.Column("tax_rate", sa.Numeric(5, 2), default=15.0),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # members
    op.create_table("members",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("member_id", sa.String(20), unique=True, nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("gender", sa.String(10), nullable=True),
        sa.Column("national_id", sa.String(20), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("emergency_contact_name", sa.String(255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(20), nullable=True),
        sa.Column("emergency_contact_relation", sa.String(50), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("qr_code", sa.String(255), unique=True, nullable=True),
        sa.Column("rfid_tag", sa.String(100), unique=True, nullable=True),
        sa.Column("pin_code", sa.String(6), nullable=True),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("medical_notes", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("referred_by_id", sa.Integer, sa.ForeignKey("members.id"), nullable=True),
        sa.Column("total_checkins", sa.Integer, default=0),
        sa.Column("lifetime_value", sa.Integer, default=0),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_members_member_id", "members", ["member_id"])
    op.create_index("ix_members_email", "members", ["email"])
    op.create_index("ix_members_status", "members", ["status"])

    # memberships
    op.create_table("memberships",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("members.id"), nullable=False),
        sa.Column("plan_id", sa.Integer, sa.ForeignKey("membership_plans.id"), nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("price_paid", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(10, 2), default=0),
        sa.Column("freeze_days_used", sa.Integer, default=0),
        sa.Column("freeze_start", sa.Date, nullable=True),
        sa.Column("freeze_end", sa.Date, nullable=True),
        sa.Column("freeze_reason", sa.String(255), nullable=True),
        sa.Column("auto_renew", sa.Boolean, default=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("sold_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("contract_signed", sa.Boolean, default=False),
        sa.Column("contract_url", sa.String(500), nullable=True),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # invoices
    op.create_table("invoices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("invoice_number", sa.String(30), unique=True, nullable=False),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("members.id"), nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("membership_id", sa.Integer, sa.ForeignKey("memberships.id"), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(10, 2), default=0),
        sa.Column("tax_rate", sa.Numeric(5, 2), default=15.0),
        sa.Column("tax_amount", sa.Numeric(10, 2), default=0),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("amount_paid", sa.Numeric(10, 2), default=0),
        sa.Column("amount_due", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_invoices_number", "invoices", ["invoice_number"])
    op.create_index("ix_invoices_status", "invoices", ["status"])

    # payments
    op.create_table("payments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("processed_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # attendance_logs
    op.create_table("attendance_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("members.id"), nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("check_in", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("method", sa.String(20), default="manual"),
        sa.Column("processed_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_attendance_member_date", "attendance_logs", ["member_id", "check_in"])

    # leads
    op.create_table("leads",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("source", sa.String(30), default="walk_in"),
        sa.Column("status", sa.String(20), default="new"),
        sa.Column("interest_plan_id", sa.Integer, sa.ForeignKey("membership_plans.id"), nullable=True),
        sa.Column("expected_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("assigned_to_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("next_follow_up", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("lost_reason", sa.String(255), nullable=True),
        sa.Column("converted_member_id", sa.Integer, sa.ForeignKey("members.id"), nullable=True),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # staff
    op.create_table("staff",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("employee_id", sa.String(20), unique=True, nullable=False),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("designation", sa.String(100), nullable=True),
        sa.Column("employment_type", sa.String(20), default="full_time"),
        sa.Column("base_salary", sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column("commission_rate", sa.Numeric(5, 2), default=0),
        sa.Column("hire_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("national_id", sa.String(20), nullable=True),
        sa.Column("iqama_number", sa.String(20), nullable=True),
        sa.Column("iqama_expiry", sa.Date, nullable=True),
        sa.Column("emergency_contact", sa.String(255), nullable=True),
        sa.Column("certifications", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("kpi_score", sa.Numeric(5, 2), default=0),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # staff_attendance
    op.create_table("staff_attendance",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("staff_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("check_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), default="present"),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # products
    op.create_table("products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sku", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("cost_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("sell_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock_quantity", sa.Integer, default=0),
        sa.Column("reserved_quantity", sa.Integer, default=0),
        sa.Column("reorder_level", sa.Integer, default=10),
        sa.Column("max_stock", sa.Integer, nullable=True),
        sa.Column("unit", sa.String(20), default="unit"),
        sa.Column("barcode", sa.String(50), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=True),
        sa.Column("supplier_id", sa.Integer, nullable=True),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("tax_rate", sa.Numeric(5, 2), default=15.0),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_products_sku", "products", ["sku"])

    # stock_movements
    op.create_table("stock_movements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("movement_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("quantity_before", sa.Integer, nullable=False),
        sa.Column("quantity_after", sa.Integer, nullable=False),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # purchase_orders
    op.create_table("purchase_orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("po_number", sa.String(30), unique=True, nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("supplier_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("expected_delivery", sa.Date, nullable=True),
        sa.Column("received_at", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # pos_sales
    op.create_table("pos_sales",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sale_number", sa.String(30), unique=True, nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("members.id"), nullable=True),
        sa.Column("cashier_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(10, 2), default=0),
        sa.Column("tax_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), default="completed"),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("receipt_printed", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # pos_sale_items
    op.create_table("pos_sale_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sale_id", sa.Integer, sa.ForeignKey("pos_sales.id"), nullable=False),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("product_sku", sa.String(50), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount", sa.Numeric(10, 2), default=0),
        sa.Column("line_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # class_schedules
    op.create_table("class_schedules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("trainer_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("room", sa.String(100), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer, default=20),
        sa.Column("enrolled", sa.Integer, default=0),
        sa.Column("is_recurring", sa.Boolean, default=False),
        sa.Column("recurrence_rule", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("color", sa.String(7), default="#6c63ff"),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # class_bookings
    op.create_table("class_bookings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("schedule_id", sa.Integer, sa.ForeignKey("class_schedules.id"), nullable=False),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("members.id"), nullable=False),
        sa.Column("status", sa.String(20), default="booked"),
        sa.Column("attended", sa.Boolean, default=False),
        sa.Column("waitlist_position", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # audit_logs
    op.create_table("audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("branch_id", sa.Integer, nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("old_values", postgresql.JSON, nullable=True),
        sa.Column("new_values", postgresql.JSON, nullable=True),
        sa.Column("status", sa.String(20), default="success"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # campaigns
    op.create_table("campaigns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("campaign_type", sa.String(20), nullable=False, default="sms"),
        sa.Column("status", sa.String(20), default="draft"),
        sa.Column("target_segment", sa.String(30), default="all_members"),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("message_body", sa.Text, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recipient_count", sa.Integer, default=0),
        sa.Column("sent_count", sa.Integer, default=0),
        sa.Column("delivered_count", sa.Integer, default=0),
        sa.Column("opened_count", sa.Integer, default=0),
        sa.Column("clicked_count", sa.Integer, default=0),
        sa.Column("converted_count", sa.Integer, default=0),
        sa.Column("bounced_count", sa.Integer, default=0),
        sa.Column("cost", sa.Numeric(10, 2), default=0),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # campaign_logs
    op.create_table("campaign_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("members.id"), nullable=True),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # coupons
    op.create_table("coupons",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("discount_type", sa.String(20), default="percentage"),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("min_purchase", sa.Numeric(10, 2), default=0),
        sa.Column("max_uses", sa.Integer, nullable=True),
        sa.Column("uses_count", sa.Integer, default=0),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=True),
        sa.Column("plan_id", sa.Integer, sa.ForeignKey("membership_plans.id"), nullable=True),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # payroll_runs
    op.create_table("payroll_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=True),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("pay_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), default="draft"),
        sa.Column("total_gross", sa.Numeric(10, 2), default=0),
        sa.Column("total_deductions", sa.Numeric(10, 2), default=0),
        sa.Column("total_net", sa.Numeric(10, 2), default=0),
        sa.Column("total_commissions", sa.Numeric(10, 2), default=0),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("approved_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # pay_slips
    op.create_table("pay_slips",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("payroll_runs.id"), nullable=False),
        sa.Column("staff_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=False),
        sa.Column("base_salary", sa.Numeric(10, 2), nullable=False),
        sa.Column("days_worked", sa.Integer, default=0),
        sa.Column("days_absent", sa.Integer, default=0),
        sa.Column("overtime_hours", sa.Numeric(5, 2), default=0),
        sa.Column("overtime_pay", sa.Numeric(10, 2), default=0),
        sa.Column("commission", sa.Numeric(10, 2), default=0),
        sa.Column("bonus", sa.Numeric(10, 2), default=0),
        sa.Column("gross", sa.Numeric(10, 2), nullable=False),
        sa.Column("deduction_gosi", sa.Numeric(10, 2), default=0),
        sa.Column("deduction_absence", sa.Numeric(10, 2), default=0),
        sa.Column("deduction_other", sa.Numeric(10, 2), default=0),
        sa.Column("total_deductions", sa.Numeric(10, 2), default=0),
        sa.Column("net", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_paid", sa.Boolean, default=False),
        sa.Column("paid_at", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


    # staff_shifts
    op.create_table("staff_shifts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("staff_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("shift_date", sa.Date, nullable=False),
        sa.Column("start_time", sa.String(5), nullable=False),
        sa.Column("end_time", sa.String(5), nullable=False),
        sa.Column("status", sa.String(20), default="scheduled"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_recurring", sa.Boolean, default=False),
        sa.Column("recurrence_rule", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_staff_shifts_date_branch", "staff_shifts", ["branch_id", "shift_date"])

def downgrade() -> None:
    tables = [
        "pay_slips","payroll_runs","staff_shifts","coupons","campaign_logs","campaigns",
        "audit_logs","class_bookings","class_schedules","pos_sale_items",
        "pos_sales","purchase_orders","stock_movements","products",
        "staff_attendance","staff","leads","payments","invoices",
        "memberships","attendance_logs","members","membership_plans",
        "branches","users",
    ]
    for t in tables:
        op.drop_table(t)
