"""V1 content matrix API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import content_matrix as content_matrix_service
from app.services.event_log import log_event

router = APIRouter(prefix="/content-matrixes", tags=["content_matrix"])


class ContentMatrixGenerateRequest(BaseModel):
    user_id: str
    identity_model_id: str | None = None
    pillars: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=lambda: ["xiaohongshu", "twitter"])
    formats: list[str] = Field(default_factory=lambda: ["post"])
    count_per_pillar: int = Field(default=20, ge=20, le=50)


@router.post("/generate", response_model=dict)
def generate_content_matrix(
    body: ContentMatrixGenerateRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        matrixes = content_matrix_service.generate_content_matrix(
            db=db,
            user_id=body.user_id,
            identity_model_id=body.identity_model_id,
            pillars=body.pillars,
            platforms=body.platforms,
            formats=body.formats,
            count_per_pillar=body.count_per_pillar,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "count": len(matrixes),
        "matrixes": [
            {
                "id": matrix.id,
                "pillar": matrix.pillar,
                "platform": matrix.platform,
                "format": matrix.format,
                "status": matrix.status,
                "topics_count": len(matrix.topics),
            }
            for matrix in matrixes
        ],
    }


@router.get("", response_model=list[dict])
def list_content_matrixes(
    user_id: str = Query(...),
    identity_model_id: str | None = Query(default=None),
    pillar: str | None = Query(default=None),
    platform: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    matrixes = content_matrix_service.list_content_matrixes(
        db=db,
        user_id=user_id,
        identity_model_id=identity_model_id,
        pillar=pillar,
        platform=platform,
    )
    return [
        {
            "id": matrix.id,
            "identity_model_id": matrix.identity_model_id,
            "pillar": matrix.pillar,
            "platform": matrix.platform,
            "format": matrix.format,
            "status": matrix.status,
            "topics_count": len(matrix.topics),
            "created_at": matrix.created_at.isoformat(),
        }
        for matrix in matrixes
    ]


@router.get("/{matrix_id}", response_model=dict)
def get_content_matrix(
    matrix_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    matrix = content_matrix_service.get_content_matrix(db, matrix_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="content matrix not found")
    return {
        "id": matrix.id,
        "user_id": matrix.user_id,
        "identity_model_id": matrix.identity_model_id,
        "pillar": matrix.pillar,
        "platform": matrix.platform,
        "format": matrix.format,
        "status": matrix.status,
        "topics": [
            {
                "id": topic.id,
                "title": topic.title,
                "angle": topic.angle,
                "platform": topic.platform,
                "format": topic.format,
                "status": topic.status,
                "rewrite_variants_json": topic.rewrite_variants_json,
                "rewrite_variants": topic.rewrite_variants,
            }
            for topic in matrix.topics
        ],
    }


class PublishTopicRequest(BaseModel):
    user_id: str


@router.post("/{matrix_id}/topics/{topic_id}/publish", response_model=dict)
def publish_content_topic(
    matrix_id: str,
    topic_id: str,
    body: PublishTopicRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        topic = content_matrix_service.publish_topic(
            db=db,
            matrix_id=matrix_id,
            topic_id=topic_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    log_event(
        db=db,
        user_id=body.user_id,
        event_name="content_published",
        stage="V1",
        identity_model_id=topic.identity_model_id,
        payload={"topic_id": topic.id, "matrix_id": topic.matrix_id},
    )

    return {
        "topic_id": topic.id,
        "status": topic.status,
    }
