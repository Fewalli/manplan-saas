"""areas and assets base

Revision ID: 20260308_005
Revises: 20260308_001
Create Date: 2026-03-09 00:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_005"
down_revision = "20260308_001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "areas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_areas_code_per_tenant"),
    )
    op.create_index(op.f("ix_areas_id"), "areas", ["id"], unique=False)
    op.create_index(op.f("ix_areas_tenant_id"), "areas", ["tenant_id"], unique=False)

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("area_id", sa.Integer(), sa.ForeignKey("areas.id"), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_assets_code_per_tenant"),
    )
    op.create_index(op.f("ix_assets_id"), "assets", ["id"], unique=False)
    op.create_index(op.f("ix_assets_tenant_id"), "assets", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_assets_area_id"), "assets", ["area_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_assets_area_id"), table_name="assets")
    op.drop_index(op.f("ix_assets_tenant_id"), table_name="assets")
    op.drop_index(op.f("ix_assets_id"), table_name="assets")
    op.drop_table("assets")

    op.drop_index(op.f("ix_areas_tenant_id"), table_name="areas")
    op.drop_index(op.f("ix_areas_id"), table_name="areas")
    op.drop_table("areas")