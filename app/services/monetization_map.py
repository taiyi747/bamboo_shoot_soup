"""V1 monetization map service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.monetization import MonetizationMap, MonetizationWeekNode


def generate_monetization_map(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None,
    title: str,
) -> MonetizationMap:
    map_ = MonetizationMap(
        user_id=user_id,
        identity_model_id=identity_model_id,
        title=title.strip() or "12 周变现路线图",
        status="generated",
    )
    db.add(map_)
    db.flush()

    for week_no in range(1, 13):
        db.add(
            MonetizationWeekNode(
                map_id=map_.id,
                user_id=user_id,
                week_no=week_no,
                objective=f"第 {week_no} 周目标",
                expected_output=f"第 {week_no} 周产出",
                validation_goal=f"第 {week_no} 周验证指标",
                status="pending",
            )
        )

    db.commit()
    db.refresh(map_)
    return map_


def list_monetization_maps(db: Session, *, user_id: str) -> list[MonetizationMap]:
    return (
        db.query(MonetizationMap)
        .filter(MonetizationMap.user_id == user_id)
        .order_by(MonetizationMap.created_at.desc())
        .all()
    )


def get_monetization_map(db: Session, map_id: str) -> MonetizationMap | None:
    return db.query(MonetizationMap).filter(MonetizationMap.id == map_id).first()
