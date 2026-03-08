"""work orders foundation

Revision ID: 20260308_01
Revises: 20260308_001
Create Date: 2026-03-08 18:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_01"
down_revision = "20260308_001"
branch_labels = None
depends_on = None


work_order_type = sa.Enum("OSC", "OSCP", "OSM", "OSP", "CHECKLIST", name="workordertype")
work_order_status = sa.Enum(
    "ABERTA", "EM_EXECUCAO", "SUSPENSA", "FINALIZADA", "ENCERRADA", "EXECUTADO",
    name="workorderstatus",
)
work_order_event_type = sa.Enum(
    "OPENED", "STARTED", "SUSPENDED", "RESUMED", "FINALIZED", "CLOSED", "REVISION_CREATED", "DATE_CHANGED",
    name="workordereventtype",
)


def upgrade():


    op.create_table(
        "work_order_counters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("current_value", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("tenant_id", name="uq_work_order_counters_tenant"),
    )
    op.create_index(op.f("ix_work_order_counters_tenant_id"), "work_order_counters", ["tenant_id"], unique=False)

    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("type", work_order_type, nullable=False),
        sa.Column("status", work_order_status, nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("technician_current_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("machine_stopped", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("happened_what", sa.Text(), nullable=True),
        sa.Column("happened_why", sa.Text(), nullable=True),
        sa.Column("action_taken", sa.Text(), nullable=True),
        sa.Column("technician_downtime_minutes", sa.Integer(), nullable=True),
        sa.Column("requester_downtime_minutes", sa.Integer(), nullable=True),
        sa.Column("met_expectation", sa.Boolean(), nullable=True),
        sa.Column("finalization_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_work_orders_tenant_code"),
    )
    op.create_index(op.f("ix_work_orders_id"), "work_orders", ["id"], unique=False)
    op.create_index(op.f("ix_work_orders_tenant_id"), "work_orders", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_work_orders_type"), "work_orders", ["type"], unique=False)
    op.create_index(op.f("ix_work_orders_status"), "work_orders", ["status"], unique=False)
    op.create_index(op.f("ix_work_orders_code"), "work_orders", ["code"], unique=False)
    op.create_index(op.f("ix_work_orders_requester_id"), "work_orders", ["requester_id"], unique=False)
    op.create_index(op.f("ix_work_orders_asset_id"), "work_orders", ["asset_id"], unique=False)
    op.create_index(op.f("ix_work_orders_technician_current_id"), "work_orders", ["technician_current_id"], unique=False)

    op.create_table(
        "work_order_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id"), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", work_order_event_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_work_order_events_id"), "work_order_events", ["id"], unique=False)
    op.create_index(op.f("ix_work_order_events_work_order_id"), "work_order_events", ["work_order_id"], unique=False)
    op.create_index(op.f("ix_work_order_events_actor_user_id"), "work_order_events", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_work_order_events_event_type"), "work_order_events", ["event_type"], unique=False)

    op.create_table(
        "execution_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id"), nullable=False),
        sa.Column("technician_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_execution_sessions_id"), "execution_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_execution_sessions_tenant_id"), "execution_sessions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_execution_sessions_work_order_id"), "execution_sessions", ["work_order_id"], unique=False)
    op.create_index(op.f("ix_execution_sessions_technician_id"), "execution_sessions", ["technician_id"], unique=False)

    op.execute(
        """
        CREATE UNIQUE INDEX uq_execution_sessions_active_technician
        ON execution_sessions (technician_id)
        WHERE ended_at IS NULL
        """
    )


def downgrade():
    op.drop_index("uq_execution_sessions_active_technician", table_name="execution_sessions")
    op.drop_table("execution_sessions")
    op.drop_table("work_order_events")
    op.drop_table("work_orders")
    op.drop_table("work_order_counters")

    bind = op.get_bind()
    work_order_event_type.drop(bind, checkfirst=True)
    work_order_status.drop(bind, checkfirst=True)
    work_order_type.drop(bind, checkfirst=True)