"""V2 simulator service."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.simulator import PrepublishEvaluation


def _contains_any(text: str, words: list[str]) -> bool:
    lowered = text.lower()
    return any(word.lower() in lowered for word in words)


def _score_probabilities(draft_text: str) -> tuple[float, float, float, list[str]]:
    controversy = 0.2
    brand = 0.2
    trust = 0.05
    factors: list[str] = []

    if _contains_any(draft_text, ["绝对", "保证", "内幕", "爆料", "封神"]):
        controversy += 0.35
        brand += 0.25
        trust -= 0.2
        factors.append("存在高承诺或争议性措辞")
    if _contains_any(draft_text, ["抄袭", "侵权", "冒充", "违法"]):
        controversy += 0.4
        brand += 0.45
        trust -= 0.3
        factors.append("触及合规高风险词")
    if len(draft_text.strip()) < 80:
        trust -= 0.1
        factors.append("内容长度偏短，论证不足")

    controversy = min(max(controversy, 0.01), 0.99)
    brand = min(max(brand, 0.01), 0.99)
    trust = min(max(trust, -0.95), 0.95)
    return controversy, brand, trust, factors


def _recommendation(controversy_prob: float, brand_risk: float, trust_impact: float) -> str:
    if controversy_prob >= 0.75 or brand_risk >= 0.75 or trust_impact < -0.45:
        return "暂缓"
    if controversy_prob < 0.45 and brand_risk < 0.45 and trust_impact >= -0.15:
        return "发"
    return "改后发"


def evaluate_prepublish(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None,
    draft_text: str,
    platform: str,
    stage_goal: str,
) -> PrepublishEvaluation:
    controversy_prob, brand_risk, trust_impact, factors = _score_probabilities(draft_text)
    recommendation = _recommendation(controversy_prob, brand_risk, trust_impact)
    manual_confirmation_required = recommendation == "暂缓"

    growth_min = max(0.01, 0.12 - brand_risk * 0.05)
    growth_max = min(0.95, growth_min + 0.18 - controversy_prob * 0.05)
    growth_prediction_range = f"{growth_min:.2f}-{growth_max:.2f}"

    rewrite = (
        "建议改写：删除绝对化措辞，补充证据来源，明确边界声明，并保留可执行行动建议。"
    )

    evaluation = PrepublishEvaluation(
        user_id=user_id,
        identity_model_id=identity_model_id,
        platform=platform,
        stage_goal=stage_goal,
        draft_text=draft_text,
        growth_prediction_range=growth_prediction_range,
        controversy_prob=controversy_prob,
        brand_risk=brand_risk,
        trust_impact=trust_impact,
        recommendation=recommendation,
        trigger_factors_json=json.dumps(factors, ensure_ascii=False),
        rewrite=rewrite,
        manual_confirmation_required=manual_confirmation_required,
        confirmed=False,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation
