"""Launch kit service."""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.launch_kit import LaunchKit, LaunchKitDay


def generate_launch_kit(
    db: Session,
    user_id: str,
    identity_model_id: str | None = None,
    constitution_id: str | None = None,
    sustainable_columns: list[str] | None = None,
    growth_experiment_suggestion: list[dict] | None = None,
) -> LaunchKit:
    """
    Generate 7-Day Launch Kit.
    
    Per product-spec 2.3:
    - 7 日每日主题
    - 每日内容草稿或大纲（含开头）
    - 3 个可持续栏目
    - 1 个增长实验
    """
    # Default sustainable columns
    sustainable_columns = sustainable_columns or [
        "深度干货类",
        "观点解读类",
        "互动话题类",
    ]

    # Default growth experiment
    growth_experiment_suggestion = growth_experiment_suggestion or [
        {
            "name": "发布时间测试",
            "hypothesis": "不同发布时间对互动率有显著影响",
            "variables": ["发布时间", "内容类型"],
            "duration": "7天",
            "success_metric": "互动率提升30%",
        },
    ]

    # Create kit
    kit = LaunchKit(
        user_id=user_id,
        identity_model_id=identity_model_id,
        constitution_id=constitution_id,
        sustainable_columns_json=json.dumps(sustainable_columns, ensure_ascii=False),
        growth_experiment_suggestion_json=json.dumps(
            growth_experiment_suggestion, ensure_ascii=False
        ),
    )
    db.add(kit)
    db.flush()  # Get kit.id

    # Generate 7 days content
    day_templates = [
        {
            "day_no": 1,
            "theme": "自我介绍与价值主张",
            "draft_or_outline": "开篇：我是谁，我能为你带来什么价值\n主体：为什么做这个方向\n结尾：希望和你一起成长",
            "opening_text": "你好，我是...",
        },
        {
            "day_no": 2,
            "theme": "核心方法论分享",
            "draft_or_outline": "开篇：一个常见痛点场景\n主体：3个关键步骤/要点\n结尾：总结要点+下期预告",
            "opening_text": "很多人问我是怎么...",
        },
        {
            "day_no": 3,
            "theme": "案例拆解",
            "draft_or_outline": "开篇：引入一个典型案例\n主体：案例背景、做法、结果\n结尾：从案例中提取的方法论",
            "opening_text": "今天分享一个我最近的...",
        },
        {
            "day_no": 4,
            "theme": "观点与立场",
            "draft_or_outline": "开篇：一个有争议的话题\n主体：我的观点及理由\n结尾：邀请读者评论",
            "opening_text": "我不认为...",
        },
        {
            "day_no": 5,
            "theme": "工具与资源推荐",
            "draft_or_outline": "开篇：介绍今天推荐的资源\n主体：资源特点、适用场景、使用方法\n结尾：获取方式+下期主题",
            "opening_text": "最近发现了一个很实用的...",
        },
        {
            "day_no": 6,
            "theme": "互动问答/话题讨论",
            "draft_or_outline": "开篇：提出一个讨论话题\n主体：我的看法+引导互动的问题\n结尾：下期预告",
            "opening_text": "想听听你们的想法...",
        },
        {
            "day_no": 7,
            "theme": "一周回顾与下周预告",
            "draft_or_outline": "开篇：本周内容回顾\n主体：本周收获总结\n结尾：下周内容预告+互动邀请",
            "opening_text": "这周我们聊了...",
        },
    ]

    for template in day_templates:
        day = LaunchKitDay(
            kit_id=kit.id,
            day_no=template["day_no"],
            theme=template["theme"],
            draft_or_outline=template["draft_or_outline"],
            opening_text=template["opening_text"],
        )
        db.add(day)

    db.commit()
    db.refresh(kit)
    return kit


def get_user_launch_kits(db: Session, user_id: str) -> list[LaunchKit]:
    """Get all launch kits for a user."""
    return db.query(LaunchKit).filter(LaunchKit.user_id == user_id).all()


def get_launch_kit(db: Session, kit_id: str) -> LaunchKit | None:
    """Get launch kit by ID with days."""
    return db.query(LaunchKit).filter(LaunchKit.id == kit_id).first()


def get_latest_launch_kit(db: Session, user_id: str) -> LaunchKit | None:
    """Get user's latest launch kit."""
    return (
        db.query(LaunchKit)
        .filter(LaunchKit.user_id == user_id)
        .order_by(LaunchKit.created_at.desc())
        .first()
    )
