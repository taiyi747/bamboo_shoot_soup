"""V2 viewpoint assets API routes."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import viewpoint_asset as asset_service

router = APIRouter(prefix="/viewpoint-assets", tags=["viewpoint_assets"])


class ViewpointAssetExtractRequest(BaseModel):
    user_id: str
    identity_model_id: str | None = None
    topic: str
    platform: str = "all"
    source_contents: list[str] = Field(default_factory=list)


@router.post("/extract", response_model=dict)
def extract_assets(
    body: ViewpointAssetExtractRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    contents = body.source_contents or [f"{body.topic} 历史内容样本"]
    assets = asset_service.extract_viewpoint_assets(
        db=db,
        user_id=body.user_id,
        identity_model_id=body.identity_model_id,
        source_contents=contents,
        topic=body.topic,
        platform=body.platform,
    )
    return {
        "count": len(assets),
        "assets": [
            {
                "id": asset.id,
                "topic": asset.topic,
                "platform": asset.platform,
                "stance": asset.stance,
                "summary": asset.summary,
                "tags_json": asset.tags_json,
                "tags": asset.tags,
            }
            for asset in assets
        ],
    }


@router.get("/search", response_model=list[dict])
def search_assets(
    user_id: str = Query(...),
    query: str | None = Query(default=None),
    identity_model_id: str | None = Query(default=None),
    platform: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    assets = asset_service.search_viewpoint_assets(
        db=db,
        user_id=user_id,
        query=query,
        identity_model_id=identity_model_id,
        platform=platform,
    )
    return [
        {
            "id": asset.id,
            "identity_model_id": asset.identity_model_id,
            "topic": asset.topic,
            "platform": asset.platform,
            "stance": asset.stance,
            "summary": asset.summary,
            "tags_json": asset.tags_json,
            "tags": asset.tags,
            "cases": [{"id": case.id, "title": case.title, "description": case.description} for case in asset.cases],
            "frameworks": [
                {"id": fw.id, "name": fw.name, "steps_json": fw.steps_json, "steps": fw.steps}
                for fw in asset.frameworks
            ],
            "faq_items": [
                {"id": faq.id, "question": faq.question, "answer": faq.answer}
                for faq in asset.faq_items
            ],
            "created_at": asset.created_at.isoformat(),
        }
        for asset in assets
    ]
