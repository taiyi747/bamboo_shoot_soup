"""Content matrix API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.content_matrix import ContentMatrixGenerate, ContentMatrixResponse
from app.services import content_matrix as content_matrix_service
from app.services.llm_client import LLMServiceError

router = APIRouter(prefix="/content-matrices", tags=["content_matrix"])


@router.post("/generate", response_model=dict)
def generate_content_matrix(
    body: ContentMatrixGenerate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        matrix, degraded, degrade_reason = content_matrix_service.generate_content_matrix(
            db,
            user_id=body.user_id,
            identity_model_id=body.identity_model_id,
            constitution_id=body.constitution_id,
            hints=body.hints,
        )
    except LLMServiceError as error:
        raise HTTPException(status_code=502, detail=error.to_detail()) from error

    return {
        "id": matrix.id,
        "user_id": matrix.user_id,
        "identity_model_id": matrix.identity_model_id,
        "constitution_id": matrix.constitution_id,
        "degraded": degraded,
        "degrade_reason": degrade_reason,
    }


@router.get("/users/{user_id}", response_model=list[ContentMatrixResponse])
def get_user_content_matrices(
    user_id: str,
    db: Session = Depends(get_db),
) -> list[ContentMatrixResponse]:
    return content_matrix_service.get_user_content_matrices(db, user_id)


@router.get("/{matrix_id}", response_model=ContentMatrixResponse)
def get_content_matrix(
    matrix_id: str,
    db: Session = Depends(get_db),
) -> ContentMatrixResponse:
    matrix = content_matrix_service.get_content_matrix(db, matrix_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="Content matrix not found")
    return matrix
