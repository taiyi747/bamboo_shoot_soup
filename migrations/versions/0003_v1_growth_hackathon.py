"""Add V1 growth tables and replay cache.

Revision ID: 0003_v1_growth_hackathon
Revises: 0002_mvp_full
Create Date: 2026-02-25 09:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_v1_growth_hackathon"
down_revision: Union[str, Sequence[str], None] = "0002_mvp_full"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_matrices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("constitution_id", sa.String(length=36), nullable=True),
        sa.Column("content_pillars_json", sa.Text(), nullable=True),
        sa.Column("matrix_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["identity_model_id"], ["identity_models.id"]),
        sa.ForeignKeyConstraint(["constitution_id"], ["persona_constitutions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_matrices_user_id", "content_matrices", ["user_id"])

    op.create_table(
        "experiments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("hypothesis", sa.Text(), nullable=True),
        sa.Column("variables_json", sa.Text(), nullable=True),
        sa.Column("execution_cycle", sa.String(length=120), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("conclusion", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["identity_model_id"], ["identity_models.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_experiments_user_id", "experiments", ["user_id"])

    op.create_table(
        "monetization_maps",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("constitution_id", sa.String(length=36), nullable=True),
        sa.Column("primary_path", sa.Text(), nullable=True),
        sa.Column("backup_path", sa.Text(), nullable=True),
        sa.Column("weeks_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["identity_model_id"], ["identity_models.id"]),
        sa.ForeignKeyConstraint(["constitution_id"], ["persona_constitutions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monetization_maps_user_id", "monetization_maps", ["user_id"])

    op.create_table(
        "llm_generation_replays",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("operation", sa.String(length=100), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_llm_generation_replays_user_operation",
        "llm_generation_replays",
        ["user_id", "operation"],
    )


def downgrade() -> None:
    op.drop_table("llm_generation_replays")
    op.drop_table("monetization_maps")
    op.drop_table("experiments")
    op.drop_table("content_matrices")
