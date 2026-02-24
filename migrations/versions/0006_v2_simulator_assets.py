"""Add V2 simulator and viewpoint asset tables.

Revision ID: 0006_v2_simulator_assets
Revises: 0005_v1_monetization_portfolio
Create Date: 2026-02-25 00:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_v2_simulator_assets"
down_revision: Union[str, Sequence[str], None] = "0005_v1_monetization_portfolio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prepublish_evaluations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("stage_goal", sa.String(length=100), nullable=False),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("growth_prediction_range", sa.String(length=50), nullable=False),
        sa.Column("controversy_prob", sa.Float(), nullable=False),
        sa.Column("brand_risk", sa.Float(), nullable=False),
        sa.Column("trust_impact", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(length=20), nullable=False),
        sa.Column("trigger_factors_json", sa.Text(), nullable=False),
        sa.Column("rewrite", sa.Text(), nullable=False),
        sa.Column("manual_confirmation_required", sa.Boolean(), nullable=False),
        sa.Column("confirmed", sa.Boolean(), nullable=False),
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
    op.create_index("ix_prepublish_evaluations_user_id", "prepublish_evaluations", ["user_id"])
    op.create_index(
        "ix_prepublish_evaluations_identity_platform",
        "prepublish_evaluations",
        ["identity_model_id", "platform"],
    )

    op.create_table(
        "viewpoint_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("topic", sa.String(length=120), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("stance", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.Text(), nullable=False),
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
    op.create_index("ix_viewpoint_assets_user_id", "viewpoint_assets", ["user_id"])
    op.create_index("ix_viewpoint_assets_topic", "viewpoint_assets", ["topic"])

    op.create_table(
        "asset_cases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["viewpoint_assets.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asset_cases_user_id", "asset_cases", ["user_id"])

    op.create_table(
        "asset_frameworks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("steps_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["viewpoint_assets.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asset_frameworks_user_id", "asset_frameworks", ["user_id"])

    op.create_table(
        "faq_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["viewpoint_assets.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_faq_items_user_id", "faq_items", ["user_id"])


def downgrade() -> None:
    op.drop_table("faq_items")
    op.drop_table("asset_frameworks")
    op.drop_table("asset_cases")
    op.drop_table("viewpoint_assets")
    op.drop_table("prepublish_evaluations")
