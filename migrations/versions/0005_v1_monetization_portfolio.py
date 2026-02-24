"""Add V1 monetization and identity portfolio tables.

Revision ID: 0005_v1_monetization_portfolio
Revises: 0004_v1_content_experiment
Create Date: 2026-02-25 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_v1_monetization_portfolio"
down_revision: Union[str, Sequence[str], None] = "0004_v1_content_experiment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monetization_maps",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["identity_model_id"], ["identity_models.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monetization_maps_user_id", "monetization_maps", ["user_id"])

    op.create_table(
        "monetization_week_nodes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("map_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("week_no", sa.Integer(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("validation_goal", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["map_id"], ["monetization_maps.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monetization_week_nodes_user_id", "monetization_week_nodes", ["user_id"])
    with op.batch_alter_table("monetization_week_nodes") as batch:
        batch.create_check_constraint(
            "ck_monetization_week_nodes_week_no_range",
            "week_no >= 1 AND week_no <= 12",
        )
        batch.create_unique_constraint("uq_monetization_week_nodes_map_week_no", ["map_id", "week_no"])

    op.create_table(
        "identity_portfolios",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("primary_identity_id", sa.String(length=36), nullable=False),
        sa.Column("backup_identity_id", sa.String(length=36), nullable=True),
        sa.Column("anonymous_identity", sa.Text(), nullable=False),
        sa.Column("tool_identity", sa.Text(), nullable=False),
        sa.Column("conflict_avoidance", sa.Text(), nullable=False),
        sa.Column("asset_reuse_strategy", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["backup_identity_id"], ["identity_models.id"]),
        sa.ForeignKeyConstraint(["primary_identity_id"], ["identity_models.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_identity_portfolios_user_id", "identity_portfolios", ["user_id"])
    with op.batch_alter_table("identity_portfolios") as batch:
        batch.create_check_constraint(
            "ck_identity_portfolios_primary_backup_diff",
            "(backup_identity_id IS NULL) OR (primary_identity_id <> backup_identity_id)",
        )


def downgrade() -> None:
    with op.batch_alter_table("identity_portfolios") as batch:
        batch.drop_constraint("ck_identity_portfolios_primary_backup_diff", type_="check")
    op.drop_table("identity_portfolios")

    with op.batch_alter_table("monetization_week_nodes") as batch:
        batch.drop_constraint("uq_monetization_week_nodes_map_week_no", type_="unique")
        batch.drop_constraint("ck_monetization_week_nodes_week_no_range", type_="check")
    op.drop_table("monetization_week_nodes")
    op.drop_table("monetization_maps")
