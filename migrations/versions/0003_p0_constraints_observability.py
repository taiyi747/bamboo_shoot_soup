"""Add P0 constraints and llm call observability table.

Revision ID: 0003_p0_constraints_observability
Revises: 0002_mvp_full
Create Date: 2026-02-24 23:50:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_p0_constraints_observability"
down_revision: Union[str, Sequence[str], None] = "0002_mvp_full"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("onboarding_sessions") as batch:
        batch.create_foreign_key(
            "fk_onboarding_sessions_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )

    with op.batch_alter_table("capability_profiles") as batch:
        batch.create_foreign_key(
            "fk_capability_profiles_session_id_onboarding_sessions",
            "onboarding_sessions",
            ["session_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_capability_profiles_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )
        batch.create_unique_constraint("uq_capability_profiles_session_id", ["session_id"])

    with op.batch_alter_table("identity_models") as batch:
        batch.create_foreign_key("fk_identity_models_user_id_users", "users", ["user_id"], ["id"])
        batch.create_foreign_key(
            "fk_identity_models_session_id_onboarding_sessions",
            "onboarding_sessions",
            ["session_id"],
            ["id"],
        )

    with op.batch_alter_table("identity_selections") as batch:
        batch.create_foreign_key(
            "fk_identity_selections_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_identity_selections_primary_identity_id_identity_models",
            "identity_models",
            ["primary_identity_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_identity_selections_backup_identity_id_identity_models",
            "identity_models",
            ["backup_identity_id"],
            ["id"],
        )
        batch.create_check_constraint(
            "ck_identity_selections_primary_backup_diff",
            "(backup_identity_id IS NULL) OR (primary_identity_id <> backup_identity_id)",
        )

    with op.batch_alter_table("persona_constitutions") as batch:
        batch.create_foreign_key(
            "fk_persona_constitutions_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_persona_constitutions_identity_model_id_identity_models",
            "identity_models",
            ["identity_model_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_persona_constitutions_previous_version_id_persona_constitutions",
            "persona_constitutions",
            ["previous_version_id"],
            ["id"],
        )

    with op.batch_alter_table("risk_boundary_items") as batch:
        batch.create_foreign_key(
            "fk_risk_boundary_items_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_risk_boundary_items_identity_model_id_identity_models",
            "identity_models",
            ["identity_model_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_risk_boundary_items_constitution_id_persona_constitutions",
            "persona_constitutions",
            ["constitution_id"],
            ["id"],
        )

    with op.batch_alter_table("launch_kits") as batch:
        batch.create_foreign_key("fk_launch_kits_user_id_users", "users", ["user_id"], ["id"])
        batch.create_foreign_key(
            "fk_launch_kits_identity_model_id_identity_models",
            "identity_models",
            ["identity_model_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_launch_kits_constitution_id_persona_constitutions",
            "persona_constitutions",
            ["constitution_id"],
            ["id"],
        )

    with op.batch_alter_table("launch_kit_days") as batch:
        batch.create_foreign_key(
            "fk_launch_kit_days_kit_id_launch_kits",
            "launch_kits",
            ["kit_id"],
            ["id"],
        )
        batch.create_unique_constraint("uq_launch_kit_days_kit_id_day_no", ["kit_id", "day_no"])

    with op.batch_alter_table("consistency_checks") as batch:
        batch.create_foreign_key(
            "fk_consistency_checks_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_consistency_checks_identity_model_id_identity_models",
            "identity_models",
            ["identity_model_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_consistency_checks_constitution_id_persona_constitutions",
            "persona_constitutions",
            ["constitution_id"],
            ["id"],
        )
        batch.create_check_constraint(
            "ck_consistency_checks_risk_warning_when_triggered",
            "(risk_triggered = 0) OR (length(trim(coalesce(risk_warning, ''))) > 0)",
        )

    with op.batch_alter_table("event_logs") as batch:
        batch.create_foreign_key("fk_event_logs_user_id_users", "users", ["user_id"], ["id"])
        batch.create_foreign_key(
            "fk_event_logs_identity_model_id_identity_models",
            "identity_models",
            ["identity_model_id"],
            ["id"],
        )
        batch.create_check_constraint(
            "ck_event_logs_stage",
            "stage IN ('MVP', 'V1', 'V2')",
        )

    op.create_table(
        "llm_call_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("operation", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("retry", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("request_id", sa.String(length=200), nullable=True),
        sa.Column("provider_status", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_call_logs_user_id", "llm_call_logs", ["user_id"])
    op.create_index("ix_llm_call_logs_operation", "llm_call_logs", ["operation"])
    op.create_index("ix_llm_call_logs_code", "llm_call_logs", ["code"])
    op.create_index("ix_llm_call_logs_created_at", "llm_call_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("llm_call_logs")

    with op.batch_alter_table("event_logs") as batch:
        batch.drop_constraint("ck_event_logs_stage", type_="check")
        batch.drop_constraint("fk_event_logs_identity_model_id_identity_models", type_="foreignkey")
        batch.drop_constraint("fk_event_logs_user_id_users", type_="foreignkey")

    with op.batch_alter_table("consistency_checks") as batch:
        batch.drop_constraint("ck_consistency_checks_risk_warning_when_triggered", type_="check")
        batch.drop_constraint("fk_consistency_checks_constitution_id_persona_constitutions", type_="foreignkey")
        batch.drop_constraint("fk_consistency_checks_identity_model_id_identity_models", type_="foreignkey")
        batch.drop_constraint("fk_consistency_checks_user_id_users", type_="foreignkey")

    with op.batch_alter_table("launch_kit_days") as batch:
        batch.drop_constraint("uq_launch_kit_days_kit_id_day_no", type_="unique")
        batch.drop_constraint("fk_launch_kit_days_kit_id_launch_kits", type_="foreignkey")

    with op.batch_alter_table("launch_kits") as batch:
        batch.drop_constraint("fk_launch_kits_constitution_id_persona_constitutions", type_="foreignkey")
        batch.drop_constraint("fk_launch_kits_identity_model_id_identity_models", type_="foreignkey")
        batch.drop_constraint("fk_launch_kits_user_id_users", type_="foreignkey")

    with op.batch_alter_table("risk_boundary_items") as batch:
        batch.drop_constraint("fk_risk_boundary_items_constitution_id_persona_constitutions", type_="foreignkey")
        batch.drop_constraint("fk_risk_boundary_items_identity_model_id_identity_models", type_="foreignkey")
        batch.drop_constraint("fk_risk_boundary_items_user_id_users", type_="foreignkey")

    with op.batch_alter_table("persona_constitutions") as batch:
        batch.drop_constraint(
            "fk_persona_constitutions_previous_version_id_persona_constitutions",
            type_="foreignkey",
        )
        batch.drop_constraint("fk_persona_constitutions_identity_model_id_identity_models", type_="foreignkey")
        batch.drop_constraint("fk_persona_constitutions_user_id_users", type_="foreignkey")

    with op.batch_alter_table("identity_selections") as batch:
        batch.drop_constraint("ck_identity_selections_primary_backup_diff", type_="check")
        batch.drop_constraint("fk_identity_selections_backup_identity_id_identity_models", type_="foreignkey")
        batch.drop_constraint("fk_identity_selections_primary_identity_id_identity_models", type_="foreignkey")
        batch.drop_constraint("fk_identity_selections_user_id_users", type_="foreignkey")

    with op.batch_alter_table("identity_models") as batch:
        batch.drop_constraint("fk_identity_models_session_id_onboarding_sessions", type_="foreignkey")
        batch.drop_constraint("fk_identity_models_user_id_users", type_="foreignkey")

    with op.batch_alter_table("capability_profiles") as batch:
        batch.drop_constraint("uq_capability_profiles_session_id", type_="unique")
        batch.drop_constraint("fk_capability_profiles_user_id_users", type_="foreignkey")
        batch.drop_constraint("fk_capability_profiles_session_id_onboarding_sessions", type_="foreignkey")

    with op.batch_alter_table("onboarding_sessions") as batch:
        batch.drop_constraint("fk_onboarding_sessions_user_id_users", type_="foreignkey")
