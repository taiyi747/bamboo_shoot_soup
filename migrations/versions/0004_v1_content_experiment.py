"""Add V1 content matrix and growth experiments tables.

Revision ID: 0004_v1_content_experiment
Revises: 0003_p0_constraints_observability
Create Date: 2026-02-24 23:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_v1_content_experiment"
down_revision: Union[str, Sequence[str], None] = "0003_p0_constraints_observability"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_matrixes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("pillar", sa.String(length=120), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("format", sa.String(length=50), nullable=False),
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
    op.create_index("ix_content_matrixes_user_id", "content_matrixes", ["user_id"])
    op.create_index(
        "ix_content_matrixes_identity_platform_status",
        "content_matrixes",
        ["identity_model_id", "platform", "status"],
    )

    op.create_table(
        "content_topics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("matrix_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("angle", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("format", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("rewrite_variants_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["identity_model_id"], ["identity_models.id"]),
        sa.ForeignKeyConstraint(["matrix_id"], ["content_matrixes.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_topics_user_id", "content_topics", ["user_id"])
    op.create_index(
        "ix_content_topics_identity_platform_status",
        "content_topics",
        ["identity_model_id", "platform", "status"],
    )

    op.create_table(
        "growth_experiments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("variables_json", sa.Text(), nullable=False),
        sa.Column("duration", sa.String(length=80), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("conclusion", sa.Text(), nullable=False),
        sa.Column("next_iteration", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["identity_model_id"], ["identity_models.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growth_experiments_user_id", "growth_experiments", ["user_id"])
    op.create_index(
        "ix_growth_experiments_identity_status",
        "growth_experiments",
        ["identity_model_id", "status"],
    )
    with op.batch_alter_table("growth_experiments") as batch:
        batch.create_check_constraint(
            "ck_growth_experiments_next_iteration_requires_conclusion",
            "(length(trim(next_iteration)) = 0) OR (length(trim(conclusion)) > 0)",
        )


def downgrade() -> None:
    with op.batch_alter_table("growth_experiments") as batch:
        batch.drop_constraint(
            "ck_growth_experiments_next_iteration_requires_conclusion",
            type_="check",
        )
    op.drop_table("growth_experiments")
    op.drop_table("content_topics")
    op.drop_table("content_matrixes")
