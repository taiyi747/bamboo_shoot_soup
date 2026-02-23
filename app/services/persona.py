"""Persona constitution service."""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.persona import PersonaConstitution, RiskBoundaryItem


def generate_constitution(
    db: Session,
    user_id: str,
    identity_model_id: str | None = None,
    common_words: list[str] | None = None,
    forbidden_words: list[str] | None = None,
) -> PersonaConstitution:
    """
    Generate persona constitution based on identity model.
    
    Per product-spec 2.3:
    - 口吻词典（常用词、禁用词、句式偏好）
    - 观点护城河（3条不可动摇立场）
    - 叙事主线（长期动机）
    - 成长Arc（阶段叙事模板）
    """
    # Use provided words or generate defaults
    common_words = common_words or ["我", "你", "我们", "其实", "真的"]
    forbidden_words = forbidden_words or ["绝对", "一定", "必须", "保证", "没问题"]

    # Sample sentence preferences
    sentence_preferences = [
        "用短句，保持简洁",
        "多用具体案例，少讲道理",
        "适当使用问句增加互动",
        "避免说教语气",
        "保持真诚，不装",
    ]

    # Sample moat positions (观点护城河)
    moat_positions = [
        "坚持长期主义，不追求短期爆红",
        "内容必须有实际价值，拒绝水货",
        "保持独立思考，不人云亦云",
    ]

    # Sample narrative mainline
    narrative_mainline = "帮助职场人和创业者找到适合自己的成长路径，通过真实经验分享和实用方法论，让每个人都能建立可复用的个人品牌资产。"

    # Sample growth arc
    growth_arc = """
    第一阶段（0-3个月）：建立认知，完成从0到1的内容尝试
    - 确定内容方向和固定栏目
    - 找到适合自己的表达方式
    - 积累第一批粉丝
    
    第二阶段（3-6个月）：形成风格，建立个人品牌认知
    - 固化内容风格和系列
    - 尝试多平台分发
    - 开始小规模变现尝试
    
    第三阶段（6-12个月）：扩大影响，探索变现路径
    - 形成稳定的内容产出流水线
    - 开发付费产品或服务
    - 建立个人品牌资产
    """

    # Check for previous version
    previous = (
        db.query(PersonaConstitution)
        .filter(PersonaConstitution.user_id == user_id)
        .order_by(PersonaConstitution.version.desc())
        .first()
    )
    previous_version_id = previous.id if previous else None
    new_version = (previous.version + 1) if previous else 1

    constitution = PersonaConstitution(
        user_id=user_id,
        identity_model_id=identity_model_id,
        common_words_json=json.dumps(common_words, ensure_ascii=False),
        forbidden_words_json=json.dumps(forbidden_words, ensure_ascii=False),
        sentence_preferences_json=json.dumps(sentence_preferences, ensure_ascii=False),
        moat_positions_json=json.dumps(moat_positions, ensure_ascii=False),
        narrative_mainline=narrative_mainline,
        growth_arc_template=growth_arc,
        version=new_version,
        previous_version_id=previous_version_id,
    )
    db.add(constitution)
    db.commit()
    db.refresh(constitution)
    return constitution


def get_user_constitutions(db: Session, user_id: str) -> list[PersonaConstitution]:
    """Get all persona constitutions for a user."""
    return (
        db.query(PersonaConstitution)
        .filter(PersonaConstitution.user_id == user_id)
        .order_by(PersonaConstitution.version.desc())
        .all()
    )


def get_constitution(db: Session, constitution_id: str) -> PersonaConstitution | None:
    """Get constitution by ID."""
    return db.query(PersonaConstitution).filter(PersonaConstitution.id == constitution_id).first()


def get_latest_constitution(db: Session, user_id: str) -> PersonaConstitution | None:
    """Get user's latest constitution."""
    return (
        db.query(PersonaConstitution)
        .filter(PersonaConstitution.user_id == user_id)
        .order_by(PersonaConstitution.version.desc())
        .first()
    )


def create_risk_boundary(
    db: Session,
    user_id: str,
    risk_level: int,
    boundary_type: str,
    statement: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
    source: str = "user_input",
) -> RiskBoundaryItem:
    """Create a risk boundary item."""
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


def get_user_risk_boundaries(db: Session, user_id: str) -> list[RiskBoundaryItem]:
    """Get all risk boundaries for a user."""
    return db.query(RiskBoundaryItem).filter(RiskBoundaryItem.user_id == user_id).all()
