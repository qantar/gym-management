"""Performance indexes

Revision ID: 002_indexes
Revises: 001_initial
Create Date: 2026-06-13 12:01:00.000000
"""
from alembic import op

revision = "002_indexes"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite indexes for common queries
    op.create_index("ix_attendance_branch_date", "attendance_logs", ["branch_id", "check_in"])
    op.create_index("ix_attendance_checkout", "attendance_logs", ["check_out"])
    op.create_index("ix_invoices_due_date", "invoices", ["due_date"])
    op.create_index("ix_invoices_member", "invoices", ["member_id", "status"])
    op.create_index("ix_memberships_member_status", "memberships", ["member_id", "status"])
    op.create_index("ix_memberships_end_date", "memberships", ["end_date"])
    op.create_index("ix_leads_status_branch", "leads", ["status", "branch_id"])
    op.create_index("ix_leads_assigned_to", "leads", ["assigned_to_id"])
    op.create_index("ix_members_branch_status", "members", ["branch_id", "status"])
    op.create_index("ix_pos_sales_branch_date", "pos_sales", ["branch_id", "created_at"])
    op.create_index("ix_staff_branch", "staff", ["branch_id"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])
    op.create_index("ix_payroll_runs_branch_period", "payroll_runs", ["branch_id", "period_start"])
    # Trigram index for name search
    op.execute("CREATE INDEX IF NOT EXISTS ix_members_name_trgm ON members USING gin ((first_name || ' ' || last_name) gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_name_trgm ON products USING gin (name gin_trgm_ops)")


def downgrade() -> None:
    indexes = [
        ("attendance_logs", "ix_attendance_branch_date"),
        ("attendance_logs", "ix_attendance_checkout"),
        ("invoices", "ix_invoices_due_date"),
        ("invoices", "ix_invoices_member"),
        ("memberships", "ix_memberships_member_status"),
        ("memberships", "ix_memberships_end_date"),
        ("leads", "ix_leads_status_branch"),
        ("leads", "ix_leads_assigned_to"),
        ("members", "ix_members_branch_status"),
        ("pos_sales", "ix_pos_sales_branch_date"),
        ("staff", "ix_staff_branch"),
        ("campaigns", "ix_campaigns_status"),
        ("payroll_runs", "ix_payroll_runs_branch_period"),
    ]
    for table, idx in indexes:
        op.drop_index(idx, table_name=table)
    op.execute("DROP INDEX IF EXISTS ix_members_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_products_name_trgm")
