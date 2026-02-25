from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.consistency_check import ConsistencyCheck, EventLog
from app.models.identity_model import IdentityModel
from app.models.launch_kit import LaunchKit, LaunchKitDay
from app.models.onboarding import CapabilityProfile, OnboardingSession
from app.models.persona import PersonaConstitution, RiskBoundaryItem
from app.models.v1_growth import ContentMatrix, Experiment, MonetizationMap


def create_onboarding_session(
    db: Session,
    *,
    user_id: str,
    status: str = "completed",
    questionnaire_responses: dict | None = None,
) -> OnboardingSession:
    session = OnboardingSession(
        user_id=user_id,
        status=status,
        questionnaire_responses=json.dumps(questionnaire_responses or {}, ensure_ascii=False),
        completed_at=datetime.now(timezone.utc) if status == "completed" else None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_capability_profile(
    db: Session,
    *,
    session_id: str,
    user_id: str,
    skill_stack: list[str] | None = None,
    risk_tolerance: int = 3,
    time_investment_hours: int = 5,
) -> CapabilityProfile:
    profile = CapabilityProfile(
        session_id=session_id,
        user_id=user_id,
        skill_stack_json=json.dumps(skill_stack or ["python"], ensure_ascii=False),
        interest_energy_curve_json=json.dumps([{"topic": "tech", "score": 4}], ensure_ascii=False),
        cognitive_style="structured",
        value_boundaries_json=json.dumps(["no fake claims"], ensure_ascii=False),
        risk_tolerance=risk_tolerance,
        time_investment_hours=time_investment_hours,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def create_identity_model(
    db: Session,
    *,
    user_id: str,
    title: str = "Identity",
    session_id: str | None = None,
    is_primary: bool = False,
    is_backup: bool = False,
) -> IdentityModel:
    model = IdentityModel(
        user_id=user_id,
        session_id=session_id,
        title=title,
        target_audience_pain="low output consistency",
        content_pillars_json=json.dumps(["pillar1", "pillar2", "pillar3"], ensure_ascii=False),
        tone_keywords_json=json.dumps(["calm", "clear"], ensure_ascii=False),
        tone_examples_json=json.dumps(["e1", "e2", "e3", "e4", "e5"], ensure_ascii=False),
        long_term_views_json=json.dumps(["v1", "v2", "v3", "v4", "v5"], ensure_ascii=False),
        differentiation="data-backed iteration",
        growth_path_0_3m="weekly publishing",
        growth_path_3_12m="productized services",
        monetization_validation_order_json=json.dumps(["lead", "pilot"], ensure_ascii=False),
        risk_boundary_json=json.dumps(["no impersonation"], ensure_ascii=False),
        is_primary=is_primary,
        is_backup=is_backup,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def create_persona_constitution(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None = None,
    version: int = 1,
    previous_version_id: str | None = None,
) -> PersonaConstitution:
    constitution = PersonaConstitution(
        user_id=user_id,
        identity_model_id=identity_model_id,
        common_words_json=json.dumps(["focus", "iterate", "clarity"], ensure_ascii=False),
        forbidden_words_json=json.dumps(["guarantee", "overnight", "secret"], ensure_ascii=False),
        sentence_preferences_json=json.dumps(["short intro", "one claim", "one action"], ensure_ascii=False),
        moat_positions_json=json.dumps(["evidence first", "ethics bound", "repeatability"], ensure_ascii=False),
        narrative_mainline="Teach systems for steady creator growth.",
        growth_arc_template="Problem -> Method -> Evidence -> Next step",
        version=version,
        previous_version_id=previous_version_id,
    )
    db.add(constitution)
    db.commit()
    db.refresh(constitution)
    return constitution


def create_risk_boundary_item(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
    risk_level: int = 3,
    boundary_type: str = "platform",
    statement: str = "Do not fabricate results.",
    source: str = "user_input",
) -> RiskBoundaryItem:
    item = RiskBoundaryItem(
        user_id=user_id,
        identity_model_id=identity_model_id,
        constitution_id=constitution_id,
        risk_level=risk_level,
        boundary_type=boundary_type,
        statement=statement,
        source=source,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_launch_kit(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
    created_at: datetime | None = None,
) -> LaunchKit:
    kit = LaunchKit(
        user_id=user_id,
        identity_model_id=identity_model_id,
        constitution_id=constitution_id,
        sustainable_columns_json=json.dumps(["col1", "col2", "col3"], ensure_ascii=False),
        growth_experiment_suggestion_json=json.dumps([{"name": "exp1"}], ensure_ascii=False),
    )
    if created_at is not None:
        kit.created_at = created_at
    db.add(kit)
    db.flush()
    for day_no in range(1, 8):
        db.add(
            LaunchKitDay(
                kit_id=kit.id,
                day_no=day_no,
                theme=f"Theme {day_no}",
                draft_or_outline=f"Draft {day_no}",
                opening_text=f"Opening {day_no}",
            )
        )
    db.commit()
    db.refresh(kit)
    return kit


def create_consistency_check(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
    created_at: datetime | None = None,
) -> ConsistencyCheck:
    check = ConsistencyCheck(
        user_id=user_id,
        identity_model_id=identity_model_id,
        constitution_id=constitution_id,
        draft_text="draft text",
        deviation_items_json=json.dumps(["item-1"], ensure_ascii=False),
        deviation_reasons_json=json.dumps(["reason-1"], ensure_ascii=False),
        suggestions_json=json.dumps(["suggestion-1"], ensure_ascii=False),
        risk_triggered=False,
        risk_warning="",
    )
    if created_at is not None:
        check.created_at = created_at
    db.add(check)
    db.commit()
    db.refresh(check)
    return check


def create_event_log(
    db: Session,
    *,
    user_id: str,
    event_name: str,
    stage: str = "MVP",
    payload: dict | None = None,
) -> EventLog:
    event = EventLog(
        user_id=user_id,
        event_name=event_name,
        stage=stage,
        payload_json=json.dumps(payload or {}, ensure_ascii=False),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_content_matrix(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
) -> ContentMatrix:
    matrix = ContentMatrix(
        user_id=user_id,
        identity_model_id=identity_model_id,
        constitution_id=constitution_id,
        content_pillars_json=json.dumps(["pillar-1", "pillar-2", "pillar-3"], ensure_ascii=False),
        matrix_json=json.dumps(
            [
                {
                    "pillar": "pillar-1",
                    "topics": [f"topic-{i}" for i in range(1, 21)],
                    "platform_rewrites": {
                        "xiaohongshu": ["r1"],
                        "wechat": ["r2"],
                        "video_channel": ["r3"],
                    },
                }
            ],
            ensure_ascii=False,
        ),
    )
    db.add(matrix)
    db.commit()
    db.refresh(matrix)
    return matrix


def create_experiment(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None = None,
    status: str = "planned",
) -> Experiment:
    experiment = Experiment(
        user_id=user_id,
        identity_model_id=identity_model_id,
        hypothesis="CTA headline A increases save rate",
        variables_json=json.dumps(["title", "opening"], ensure_ascii=False),
        execution_cycle="7d",
        result="",
        conclusion="",
        status=status,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


def create_monetization_map(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
) -> MonetizationMap:
    monetization_map = MonetizationMap(
        user_id=user_id,
        identity_model_id=identity_model_id,
        constitution_id=constitution_id,
        primary_path="Consulting -> Cohort",
        backup_path="Template bundle",
        weeks_json=json.dumps(
            [
                {
                    "week_no": i,
                    "goal": f"goal-{i}",
                    "task": f"task-{i}",
                    "deliverable": f"deliverable-{i}",
                    "validation_metric": f"metric-{i}",
                }
                for i in range(1, 13)
            ],
            ensure_ascii=False,
        ),
    )
    db.add(monetization_map)
    db.commit()
    db.refresh(monetization_map)
    return monetization_map
