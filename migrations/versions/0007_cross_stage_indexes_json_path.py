"""Add cross-stage indexes and compatibility metadata columns.

Revision ID: 0007_cross_stage_indexes_json_path
Revises: 0006_v2_simulator_assets
Create Date: 2026-02-25 00:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_cross_stage_indexes_json_path"
down_revision: Union[str, Sequence[str], None] = "0006_v2_simulator_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_event_logs_event_name_stage_occurred_at",
        "event_logs",
        ["event_name", "stage", "occurred_at"],
    )
    op.create_index(
        "ix_content_topics_user_created_at",
        "content_topics",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_growth_experiments_user_created_at",
        "growth_experiments",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_monetization_maps_user_created_at",
        "monetization_maps",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_identity_portfolios_user_created_at",
        "identity_portfolios",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_prepublish_evaluations_user_created_at",
        "prepublish_evaluations",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_viewpoint_assets_user_created_at",
        "viewpoint_assets",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_llm_call_logs_operation_code_created_at",
        "llm_call_logs",
        ["operation", "code", "created_at"],
    )

    with op.batch_alter_table("identity_models") as batch:
        batch.add_column(
            sa.Column("legacy_json_compatible_until", sa.String(length=20), nullable=True)
        )
    with op.batch_alter_table("persona_constitutions") as batch:
        batch.add_column(
            sa.Column("legacy_json_compatible_until", sa.String(length=20), nullable=True)
        )
    with op.batch_alter_table("launch_kits") as batch:
        batch.add_column(
            sa.Column("legacy_json_compatible_until", sa.String(length=20), nullable=True)
        )
    with op.batch_alter_table("consistency_checks") as batch:
        batch.add_column(
            sa.Column("legacy_json_compatible_until", sa.String(length=20), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("consistency_checks") as batch:
        batch.drop_column("legacy_json_compatible_until")
    with op.batch_alter_table("launch_kits") as batch:
        batch.drop_column("legacy_json_compatible_until")
    with op.batch_alter_table("persona_constitutions") as batch:
        batch.drop_column("legacy_json_compatible_until")
    with op.batch_alter_table("identity_models") as batch:
        batch.drop_column("legacy_json_compatible_until")

    op.drop_index("ix_llm_call_logs_operation_code_created_at", table_name="llm_call_logs")
    op.drop_index("ix_viewpoint_assets_user_created_at", table_name="viewpoint_assets")
    op.drop_index("ix_prepublish_evaluations_user_created_at", table_name="prepublish_evaluations")
    op.drop_index("ix_identity_portfolios_user_created_at", table_name="identity_portfolios")
    op.drop_index("ix_monetization_maps_user_created_at", table_name="monetization_maps")
    op.drop_index("ix_growth_experiments_user_created_at", table_name="growth_experiments")
    op.drop_index("ix_content_topics_user_created_at", table_name="content_topics")
    op.drop_index("ix_event_logs_event_name_stage_occurred_at", table_name="event_logs")
