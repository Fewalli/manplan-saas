    """initial core

Revision ID: 0001_initial_core
Revises:
Create Date: 2026-03-07 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("slug", sa.String(length=80), nullable=False, unique=True),
        sa.Column("available_hours_per_day", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("oee_equals_availability", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("planning_window_days", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "user_account",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "email", name="uq_user_email_per_tenant"),
    )
    op.create_index("ix_user_account_tenant_id", "user_account", ["tenant_id"])

    op.create_table(
        "role",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_role_code_per_tenant"),
    )

    op.create_table(
        "user_role",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_account.id"), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("role.id"), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    op.create_table(
        "area",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("tenant_id", "name", name="uq_area_name_per_tenant"),
    )

    op.create_table(
        "asset",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("area_id", sa.Integer(), sa.ForeignKey("area.id"), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_asset_code_per_tenant"),
    )

    op.create_table(
        "work_order",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False, unique=True),
        sa.Column("base_code", sa.String(length=40), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("requester_user_id", sa.Integer(), sa.ForeignKey("user_account.id"), nullable=False),
        sa.Column("current_technician_user_id", sa.Integer(), sa.ForeignKey("user_account.id"), nullable=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("asset.id"), nullable=True),
        sa.Column("requester_name_snapshot", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("programmed_date", sa.Date(), nullable=True),
        sa.Column("happened_what", sa.Text(), nullable=True),
        sa.Column("happened_why", sa.Text(), nullable=True),
        sa.Column("done_what", sa.Text(), nullable=True),
        sa.Column("technician_stop_minutes", sa.Integer(), nullable=True),
        sa.Column("requester_stop_minutes", sa.Integer(), nullable=True),
        sa.Column("met_expectation", sa.Boolean(), nullable=True),
        sa.Column("is_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("origin_work_order_id", sa.Integer(), sa.ForeignKey("work_order.id"), nullable=True),
        sa.Column("execution_finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("window_nonconformity", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("automatic_comment", sa.Text(), nullable=True),
        sa.Column("extra_payload", sa.JSON(), nullable=True),
    )
    op.create_index("ix_work_order_code", "work_order", ["code"])
    op.create_index("ix_work_order_type", "work_order", ["type"])
    op.create_index("ix_work_order_status", "work_order", ["status"])

    op.create_table(
        "work_order_execution_session",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_order.id"), nullable=False),
        sa.Column("technician_user_id", sa.Integer(), sa.ForeignKey("user_account.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "work_order_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_order.id"), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("user_account.id"), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("work_order_event")
    op.drop_table("work_order_execution_session")
    op.drop_index("ix_work_order_status", table_name="work_order")
    op.drop_index("ix_work_order_type", table_name="work_order")
    op.drop_index("ix_work_order_code", table_name="work_order")
    op.drop_table("work_order")
    op.drop_table("asset")
    op.drop_table("area")
    op.drop_table("user_role")
    op.drop_table("role")
    op.drop_index("ix_user_account_tenant_id", table_name="user_account")
    op.drop_table("user_account")
    op.drop_table("tenant")