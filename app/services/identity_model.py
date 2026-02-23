"""Identity model service."""

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.identity_model import IdentityModel, IdentitySelection


def generate_identity_models(
    db: Session,
    user_id: str,
    session_id: str | None,
    capability_profile: dict,
    count: int = 3,
) -> list[IdentityModel]:
    """
    Generate 3-5 identity models based on capability profile.
    
    Per product-spec 2.6 business rules:
    - differentiation must be non-empty
    - tone_examples must have at least 5 sentences
    - long_term_views must have 5-10 items
    - monetization_validation_order must have at least 1 step
    """
    # In MVP, we generate sample identity models based on the capability profile
    # In production, this would call an LLM to generate real identity models
    
    skill_stack = capability_profile.get("skill_stack", [])
    cognitive_style = capability_profile.get("cognitive_style", "")
    risk_tolerance = capability_profile.get("risk_tolerance", 3)
    
    # Sample identity templates based on common creator types
    identity_templates = [
        {
            "title": "专业导师型",
            "target_audience_pain": "职场新人渴望快速成长，但缺乏系统方法论",
            "content_pillars": ["职场技能", "成长思维", "实战案例"],
            "tone_keywords": ["专业", "务实", "成长", "可落地"],
            "tone_examples": [
                "今天分享一个我亲身验证的成长方法。",
                "很多人误区是...其实应该...",
                "这三个步骤，照做就能见效。",
                "别再踩坑了，我帮你整理好了。",
                "这是最实用的职场生存指南。",
            ],
            "long_term_views": [
                "持续学习是职场生存的唯一出路",
                "方法论比运气更重要",
                "成长需要刻意练习",
                "职场是马拉松不是短跑",
                "建立个人品牌是长期资产",
            ],
            "differentiation": "以实战方法论为核心，拒绝空泛道理",
            "growth_path_0_3m": "聚焦职场基本功，建立内容框架",
            "growth_path_3_12m": "形成体系化课程，开发付费产品",
            "monetization_validation_order": ["咨询", "课程", "训练营", "社群"],
            "risk_boundary": ["不夸大效果", "不承诺结果", "遵守平台规则"],
        },
        {
            "title": "创业者视角型",
            "target_audience_pain": "有创业想法但不知如何下手，担心失败",
            "content_pillars": ["创业故事", "避坑指南", "商业模式"],
            "tone_keywords": ["真实", "深度", "反思", "经验"],
            "tone_examples": [
                "这是我踩过的第三个坑。",
                "创业最难的不是idea，而是...",
                "很多人问我为什么选择这条路。",
                "今天聊聊我最后悔的一个决定。",
                "如果你也想创业，先想清楚这三点。",
            ],
            "long_term_views": [
                "创业是认知的变现",
                "失败是最好的老师",
                "小步快跑比完美计划更重要",
                "用户需求是产品的基础",
                "现金流比估值更重要",
            ],
            "differentiation": "真实分享创业过程中的失败与反思",
            "growth_path_0_3m": "建立创业认知框架，分享踩坑经验",
            "growth_path_3_12m": "形成创业者社群，开发创业服务",
            "monetization_validation_order": ["社群", "咨询", "FA服务", "孵化"],
            "risk_boundary": ["不鼓动盲目创业", "如实描述风险", "遵守商业伦理"],
        },
        {
            "title": "生活方式型",
            "target_audience_pain": "追求工作生活平衡，希望活出自我",
            "content_pillars": ["生活理念", "工作方式", "自我探索"],
            "tone_keywords": ["平衡", "自我", "真实", "松弛"],
            "tone_examples": [
                "今天不谈工作，聊聊我最近的生活。",
                "35岁后我才明白的道理。",
                "不需要活成别人期待的样子。",
                "慢下来，才是真正的快。",
                "这是我的极简生活哲学。",
            ],
            "long_term_views": [
                "工作只是生活的一部分",
                "自我认知是一生的事业",
                "平衡比成功更重要",
                "跟随内心比追随潮流更自在",
                "生活质量不等于物质水平",
            ],
            "differentiation": "以真实生活体验为基底，拒绝鸡汤",
            "growth_path_0_3m": "分享真实生活状态，建立同好社群",
            "growth_path_3_12m": "开发生活方式产品，活的自由职业",
            "monetization_validation_order": ["产品", "广告", "联名", "咨询"],
            "risk_boundary": ["不传播消极逃避", "鼓励积极面对", "遵守法律"],
        },
        {
            "title": "技术极客型",
            "target_audience_pain": "技术人渴望提升影响力，不甘于只写代码",
            "content_pillars": ["技术深度", "思维模型", "职业发展"],
            "tone_keywords": ["技术", "深度", "思考", "产品思维"],
            "tone_examples": [
                "技术方案的选型，关键在于...",
                "从工程师到技术负责人，我走了这些弯路。",
                "代码只是手段，不是目的。",
                "今天深入聊聊这个架构设计。",
                "技术人应该具备的产品思维。",
            ],
            "long_term_views": [
                "技术是解决问题的工具",
                "工程师思维需要升级",
                "技术影响力比技术深度更重要",
                "代码质量是基本功",
                "技术人也要懂商业",
            ],
            "differentiation": "以技术深度+产品思维结合为差异化",
            "growth_path_0_3m": "分享技术干货，建立技术影响力",
            "growth_path_3_12m": "打造技术品牌，开发技术课程",
            "monetization_validation_order": ["课程", "咨询", "技术产品", "企业培训"],
            "risk_boundary": ["不夸大技术作用", "尊重技术边界", "保护商业机密"],
        },
        {
            "title": "副业探索型",
            "target_audience_pain": "有主业但想探索副业，不知道做什么",
            "content_pillars": ["副业项目", "时间管理", "变现路径"],
            "tone_keywords": ["实操", "探索", "变现", "小步尝试"],
            "tone_examples": [
                "这是我的第三个副业项目。",
                "副业真的能赚钱吗？实测给你看。",
                "我是如何用下班后3小时做副业的。",
                "这个月副业收入突破了...",
                "副业踩坑合集，看完少走弯路。",
            ],
            "long_term_views": [
                "主业求稳，副业求变",
                "小步尝试，降低试错成本",
                "副业是能力的延伸",
                "流量是最重要的资产",
                "变现需要闭环思维",
            ],
            "differentiation": "真实记录副业探索全过程，包括失败",
            "growth_path_0_3m": "尝试3-5个副业方向，找到可行路径",
            "growth_path_3_12m": "放大可行副业，形成稳定收入",
            "monetization_validation_order": ["广告", "分销", "产品", "服务"],
            "risk_boundary": ["不承诺高收益", "提示风险", "遵守平台规则"],
        },
    ]

    models = []
    for i, template in enumerate(identity_templates[:count]):
        model = IdentityModel(
            user_id=user_id,
            session_id=session_id,
            title=template["title"],
            target_audience_pain=template["target_audience_pain"],
            content_pillars_json=json.dumps(template["content_pillars"], ensure_ascii=False),
            tone_keywords_json=json.dumps(template["tone_keywords"], ensure_ascii=False),
            tone_examples_json=json.dumps(template["tone_examples"], ensure_ascii=False),
            long_term_views_json=json.dumps(template["long_term_views"], ensure_ascii=False),
            differentiation=template["differentiation"],
            growth_path_0_3m=template["growth_path_0_3m"],
            growth_path_3_12m=template["growth_path_3_12m"],
            monetization_validation_order_json=json.dumps(
                template["monetization_validation_order"], ensure_ascii=False
            ),
            risk_boundary_json=json.dumps(template["risk_boundary"], ensure_ascii=False),
        )
        db.add(model)
        models.append(model)

    db.commit()
    for model in models:
        db.refresh(model)
    return models


def select_identity(
    db: Session,
    user_id: str,
    primary_identity_id: str,
    backup_identity_id: str | None = None,
) -> IdentitySelection:
    """Save user's primary and backup identity selection."""
    # Validate IDs are different
    if backup_identity_id and primary_identity_id == backup_identity_id:
        raise ValueError("backup_identity_id must be different from primary_identity_id")

    # Validate identities exist
    primary = db.query(IdentityModel).filter(IdentityModel.id == primary_identity_id).first()
    if not primary:
        raise ValueError(f"Identity {primary_identity_id} not found")

    if backup_identity_id:
        backup = db.query(IdentityModel).filter(IdentityModel.id == backup_identity_id).first()
        if not backup:
            raise ValueError(f"Identity {backup_identity_id} not found")

    # Mark identities as primary/backup
    # First, clear previous selections for this user
    db.query(IdentityModel).filter(
        IdentityModel.user_id == user_id,
        (IdentityModel.is_primary == True) | (IdentityModel.is_backup == True)
    ).update({"is_primary": False, "is_backup": False})

    primary.is_primary = True
    if backup_identity_id:
        backup = db.query(IdentityModel).filter(IdentityModel.id == backup_identity_id).first()
        backup.is_backup = True

    # Create selection record
    selection = IdentitySelection(
        user_id=user_id,
        primary_identity_id=primary_identity_id,
        backup_identity_id=backup_identity_id,
    )
    db.add(selection)
    db.commit()
    db.refresh(selection)
    return selection


def get_user_identity_models(db: Session, user_id: str) -> list[IdentityModel]:
    """Get all identity models for a user."""
    return db.query(IdentityModel).filter(IdentityModel.user_id == user_id).all()


def get_identity_model(db: Session, model_id: str) -> IdentityModel | None:
    """Get identity model by ID."""
    return db.query(IdentityModel).filter(IdentityModel.id == model_id).first()


def get_user_selection(db: Session, user_id: str) -> IdentitySelection | None:
    """Get user's current identity selection."""
    return (
        db.query(IdentitySelection)
        .filter(IdentitySelection.user_id == user_id)
        .order_by(IdentitySelection.selected_at.desc())
        .first()
    )
