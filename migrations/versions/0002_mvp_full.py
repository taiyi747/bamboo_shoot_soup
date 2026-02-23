"""Add onboarding, identity, persona, launch_kit, consistency, and events tables

Revision ID: 0002_mvp_full
Revises: 0001_bootstrap
Create Date: 2026-02-24 01:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_mvp_full"
down_revision: Union[str, Sequence[str], None] = "0001_bootstrap"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Onboarding tables
    op.create_table(
        "onboarding_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("questionnaire_responses", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_onboarding_sessions_user_id", "onboarding_sessions", ["user_id"])
    op.create_index("ix_onboarding_sessions_status", "onboarding_sessions", ["status"])

    op.create_table(
        "capability_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("skill_stack_json", sa.Text(), nullable=True),
        sa.Column("interest_energy_curve_json", sa.Text(), nullable=True),
        sa.Column("cognitive_style", sa.String(length=500), nullable=True),
        sa.Column("value_boundaries_json", sa.Text(), nullable=True),
        sa.Column("risk_tolerance", sa.Integer(), nullable=True),
        sa.Column("time_investment_hours", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_capability_profiles_session_id", "capability_profiles", ["session_id"])
    op.create_index("ix_capability_profiles_user_id", "capability_profiles", ["user_id"])

    # Identity tables
    op.create_table(
        "identity_models",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("target_audience_pain", sa.Text(), nullable=True),
        sa.Column("content_pillars_json", sa.Text(), nullable=True),
        sa.Column("tone_keywords_json", sa.Text(), nullable=True),
        sa.Column("tone_examples_json", sa.Text(), nullable=True),
        sa.Column("long_term_views_json", sa.Text(), nullable=True),
        sa.Column("differentiation", sa.Text(), nullable=True),
        sa.Column("growth_path_0_3m", sa.Text(), nullable=True),
        sa.Column("growth_path_3_12m", sa.Text(), nullable=True),
        sa.Column("monetization_validation_order_json", sa.Text(), nullable=True),
        sa.Column("risk_boundary_json", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=True),
        sa.Column("is_backup", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_identity_models_user_id", "identity_models", ["user_id"])
    op.create_index("ix_identity_models_session_id", "identity_models", ["session_id"])

    op.create_table(
        "identity_selections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("primary_identity_id", sa.String(length=36), nullable=False),
        sa.Column("backup_identity_id", sa.String(length=36), nullable=True),
        sa.Column(
            "selected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_identity_selections_user_id", "identity_selections", ["user_id"])

    # Persona tables
    op.create_table(
        "persona_constitutions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("common_words_json", sa.Text(), nullable=True),
        sa.Column("forbidden_words_json", sa.Text(), nullable=True),
        sa.Column("sentence_preferences_json", sa.Text(), nullable=True),
        sa.Column("moat_positions_json", sa.Text(), nullable=True),
        sa.Column("narrative_mainline", sa.Text(), nullable=True),
        sa.Column("growth_arc_template", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("previous_version_id", sa.String(length=36), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_persona_constitutions_user_id", "persona_constitutions", ["user_id"])

    op.create_table(
        "risk_boundary_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("constitution_id", sa.String(length=36), nullable=True),
        sa.Column("risk_level", sa.Integer(), nullable=True),
        sa.Column("boundary_type", sa.String(length=50), nullable=True),
        sa.Column("statement", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_boundary_items_user_id", "risk_boundary_items", ["user_id"])

    # Launch kit tables
    op.create_table(
        "launch_kits",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("constitution_id", sa.String(length=36), nullable=True),
        sa.Column("sustainable_columns_json", sa.Text(), nullable=True),
        sa.Column("growth_experiment_suggestion_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_launch_kits_user_id", "launch_kits", ["user_id"])

    op.create_table(
        "launch_kit_days",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("kit_id", sa.String(length=36), nullable=False),
        sa.Column("day_no", sa.Integer(), nullable=False),
        sa.Column("theme", sa.String(length=200), nullable=True),
        sa.Column("draft_or_outline", sa.Text(), nullable=True),
        sa.Column("opening_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_launch_kit_days_kit_id", "launch_kit_days", ["kit_id"])

    # Consistency check and event log tables
    op.create_table(
        "consistency_checks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("constitution_id", sa.String(length=36), nullable=True),
        sa.Column("draft_text", sa.Text(), nullable=True),
        sa.Column("deviation_items_json", sa.Text(), nullable=True),
        sa.Column("deviation_reasons_json", sa.Text(), nullable=True),
        sa.Column("suggestions_json", sa.Text(), nullable=True),
        sa.Column("risk_triggered", sa.Boolean(), nullable=True),
        sa.Column("risk_warning", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consistency_checks_user_id", "consistency_checks", ["user_id"])

    op.create_table(
        "event_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("event_name", sa.String(length=100), nullable=False),
        sa.Column("stage", sa.String(length=10), nullable=False),
        sa.Column("identity_model_id", sa.String(length=36), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_logs_user_id", "event_logs", ["user_id"])
    op.create_index("ix_event_logs_event_name", "event_logs", ["event_name"])
    op.create_index("ix_event_logs_occurred_at", "event_logs", ["occurred_at"])


def downgrade() -> None:
    op.drop_table("event_logs")
    op.drop_table("consistency_checks")
    op.drop_table("launch_kit_days")
    op.drop_table("launch_kits")
    op.drop_table("risk_boundary_items")
    op.drop_table("persona_constitutions")
    op.drop_table("identity_selections")
    op.drop_table("identity_models")
    op.drop_table("capability_profiles")
    op.drop_table("onboarding_sessions")
