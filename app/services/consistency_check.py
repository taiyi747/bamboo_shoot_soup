"""Consistency check service."""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.consistency_check import ConsistencyCheck


def check_consistency(
    db: Session,
    user_id: str,
    draft_text: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
) -> ConsistencyCheck:
    """
    Check draft consistency against persona constitution.
    
    Per product-spec 2.6:
    - 输出必须包含：偏离项、偏离原因、修改建议
    - 若触发风险边界，必须给出明确提醒
    """
    # In MVP, we do basic keyword-based consistency checking
    # In production, this would use LLM for deeper analysis
    
    deviation_items = []
    deviation_reasons = []
    suggestions = []
    risk_triggered = False
    risk_warning = ""

    # Basic checks
    forbidden_words = ["绝对", "一定", "必须", "保证", "没问题", "轻松", "简单"]
    found_forbidden = [w for w in forbidden_words if w in draft_text]
    if found_forbidden:
        deviation_items.append("使用了禁用词汇")
        deviation_reasons.append(f"检测到可能夸大效果的词汇: {', '.join(found_forbidden)}")
        suggestions.append("建议使用更保守的表达方式")
        risk_triggered = True

    # Check draft length
    if len(draft_text) < 50:
        deviation_items.append("内容过短")
        deviation_reasons.append("内容长度不足50字，可能无法传达足够信息")
        suggestions.append("建议补充更多内容细节")

    # Check for personal pronouns (first person preferred)
    if "你" in draft_text and "我" not in draft_text:
        deviation_items.append("缺少第一人称表达")
        deviation_reasons.append("内容以第二人称为主，缺少个人经验分享")
        suggestions.append("建议加入第一人称视角的分享")

    # Risk check: platform rules violation keywords
    risk_keywords = ["加微信", "扫码", "免费领", "点击下方", "立即报名"]
    found_risk = [w for w in risk_keywords if w in draft_text]
    if found_risk:
        risk_triggered = True
        risk_warning = f"检测到可能违反平台规则的营销词汇: {', '.join(found_risk)}"

    # Check for potential legal risks
    illegal_keywords = ["保证收益", "稳赚", "必赚", "收益率"]
    found_illegal = [w for w in illegal_keywords if w in draft_text]
    if found_illegal:
        risk_triggered = True
        risk_warning = f"检测到可能涉及违规宣传的词汇: {', '.join(found_illegal)}，建议修改"

    # If everything looks good
    if not deviation_items:
        deviation_items.append("未检测到明显偏离")
        deviation_reasons.append("内容符合基本规范")
        suggestions.append("继续保持")

    check = ConsistencyCheck(
        user_id=user_id,
        identity_model_id=identity_model_id,
        constitution_id=constitution_id,
        draft_text=draft_text,
        deviation_items_json=json.dumps(deviation_items, ensure_ascii=False),
        deviation_reasons_json=json.dumps(deviation_reasons, ensure_ascii=False),
        suggestions_json=json.dumps(suggestions, ensure_ascii=False),
        risk_triggered=risk_triggered,
        risk_warning=risk_warning,
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    return check


def get_user_checks(db: Session, user_id: str) -> list[ConsistencyCheck]:
    """Get all consistency checks for a user."""
    return (
        db.query(ConsistencyCheck)
        .filter(ConsistencyCheck.user_id == user_id)
        .order_by(ConsistencyCheck.created_at.desc())
        .all()
    )


def get_check(db: Session, check_id: str) -> ConsistencyCheck | None:
    """Get consistency check by ID."""
    return db.query(ConsistencyCheck).filter(ConsistencyCheck.id == check_id).first()
