"""V1 content matrix service."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.content_matrix import ContentMatrix, ContentTopic


def generate_content_matrix(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None,
    pillars: list[str],
    platforms: list[str],
    formats: list[str],
    count_per_pillar: int,
) -> list[ContentMatrix]:
    if count_per_pillar < 20 or count_per_pillar > 50:
        raise ValueError("count_per_pillar must be between 20 and 50")
    if not pillars:
        raise ValueError("pillars must not be empty")
    if not platforms:
        raise ValueError("platforms must not be empty")
    if not formats:
        raise ValueError("formats must not be empty")

    created: list[ContentMatrix] = []
    for pillar in pillars:
        for platform in platforms:
            for format_ in formats:
                matrix = ContentMatrix(
                    user_id=user_id,
                    identity_model_id=identity_model_id,
                    pillar=pillar,
                    platform=platform,
                    format=format_,
                    status="generated",
                )
                db.add(matrix)
                db.flush()
                for idx in range(1, count_per_pillar + 1):
                    db.add(
                        ContentTopic(
                            matrix_id=matrix.id,
                            user_id=user_id,
                            identity_model_id=identity_model_id,
                            title=f"{pillar} #{idx}：{platform} {format_} 选题",
                            angle=f"从 {pillar} 切入，强调 {platform} 平台表达。",
                            platform=platform,
                            format=format_,
                            status="draft",
                            rewrite_variants_json=json.dumps(
                                [
                                    f"{platform} 版本：{pillar} 选题 {idx}",
                                    f"跨平台版本：{pillar} 选题 {idx}",
                                ],
                                ensure_ascii=False,
                            ),
                        )
                    )
                created.append(matrix)

    db.commit()
    for matrix in created:
        db.refresh(matrix)
    return created


def list_content_matrixes(
    db: Session,
    *,
    user_id: str,
    identity_model_id: str | None = None,
    pillar: str | None = None,
    platform: str | None = None,
) -> list[ContentMatrix]:
    query = db.query(ContentMatrix).filter(ContentMatrix.user_id == user_id)
    if identity_model_id:
        query = query.filter(ContentMatrix.identity_model_id == identity_model_id)
    if pillar:
        query = query.filter(ContentMatrix.pillar == pillar)
    if platform:
        query = query.filter(ContentMatrix.platform == platform)
    return query.order_by(ContentMatrix.created_at.desc()).all()


def get_content_matrix(db: Session, matrix_id: str) -> ContentMatrix | None:
    return db.query(ContentMatrix).filter(ContentMatrix.id == matrix_id).first()


def publish_topic(
    db: Session,
    *,
    matrix_id: str,
    topic_id: str,
) -> ContentTopic:
    topic = (
        db.query(ContentTopic)
        .filter(ContentTopic.id == topic_id, ContentTopic.matrix_id == matrix_id)
        .first()
    )
    if not topic:
        raise ValueError("topic not found")
    topic.status = "published"
    db.commit()
    db.refresh(topic)
    return topic
