"""V2 viewpoint asset service."""

from __future__ import annotations

import json

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.viewpoint_asset import AssetCase, AssetFramework, FaqItem, ViewpointAsset


def extract_viewpoint_assets(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None,
    source_contents: list[str],
    topic: str,
    platform: str,
) -> list[ViewpointAsset]:
    created: list[ViewpointAsset] = []
    for idx, content in enumerate(source_contents, start=1):
        summary = content.strip()[:220] if content.strip() else f"{topic} 观点摘要 {idx}"
        asset = ViewpointAsset(
            user_id=user_id,
            identity_model_id=identity_model_id,
            topic=topic,
            platform=platform,
            stance=f"{topic} 的核心立场 {idx}",
            summary=summary,
            tags_json=json.dumps([topic, platform, "auto-extracted"], ensure_ascii=False),
        )
        db.add(asset)
        db.flush()

        db.add(
            AssetCase(
                asset_id=asset.id,
                user_id=user_id,
                title=f"{topic} 案例 {idx}",
                description=f"来自历史内容的案例提炼：{summary[:80]}",
            )
        )
        db.add(
            AssetFramework(
                asset_id=asset.id,
                user_id=user_id,
                name=f"{topic} 三步框架 {idx}",
                steps_json=json.dumps(["问题定义", "方法拆解", "执行复盘"], ensure_ascii=False),
            )
        )
        db.add(
            FaqItem(
                asset_id=asset.id,
                user_id=user_id,
                question=f"{topic} 常见问题 {idx}",
                answer="先明确目标受众，再给出证据与边界。",
            )
        )
        created.append(asset)

    db.commit()
    for asset in created:
        db.refresh(asset)
    return created


def search_viewpoint_assets(
    db: Session,
    *,
    user_id: str,
    query: str | None = None,
    identity_model_id: str | None = None,
    platform: str | None = None,
) -> list[ViewpointAsset]:
    q = db.query(ViewpointAsset).filter(ViewpointAsset.user_id == user_id)
    if identity_model_id:
        q = q.filter(ViewpointAsset.identity_model_id == identity_model_id)
    if platform:
        q = q.filter(ViewpointAsset.platform == platform)
    if query:
        pattern = f"%{query}%"
        q = q.filter(
            or_(
                ViewpointAsset.topic.like(pattern),
                ViewpointAsset.summary.like(pattern),
                ViewpointAsset.stance.like(pattern),
            )
        )
    return q.order_by(ViewpointAsset.created_at.desc()).limit(100).all()
