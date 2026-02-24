"""V1 identity portfolio API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import identity_portfolio as portfolio_service

router = APIRouter(prefix="/identity-portfolios", tags=["identity_portfolio"])


class IdentityPortfolioGenerateRequest(BaseModel):
    user_id: str
    primary_identity_id: str
    backup_identity_id: str | None = None
    anonymous_identity: str = ""
    tool_identity: str = ""


@router.post("/generate", response_model=dict)
def generate_identity_portfolio(
    body: IdentityPortfolioGenerateRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        portfolio = portfolio_service.generate_identity_portfolio(
            db=db,
            user_id=body.user_id,
            primary_identity_id=body.primary_identity_id,
            backup_identity_id=body.backup_identity_id,
            anonymous_identity=body.anonymous_identity,
            tool_identity=body.tool_identity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "id": portfolio.id,
        "primary_identity_id": portfolio.primary_identity_id,
        "backup_identity_id": portfolio.backup_identity_id,
        "anonymous_identity": portfolio.anonymous_identity,
        "tool_identity": portfolio.tool_identity,
        "conflict_avoidance": portfolio.conflict_avoidance,
        "asset_reuse_strategy": portfolio.asset_reuse_strategy,
    }


@router.get("", response_model=list[dict])
def list_identity_portfolios(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    portfolios = portfolio_service.list_identity_portfolios(db=db, user_id=user_id)
    return [
        {
            "id": portfolio.id,
            "primary_identity_id": portfolio.primary_identity_id,
            "backup_identity_id": portfolio.backup_identity_id,
            "anonymous_identity": portfolio.anonymous_identity,
            "tool_identity": portfolio.tool_identity,
            "conflict_avoidance": portfolio.conflict_avoidance,
            "asset_reuse_strategy": portfolio.asset_reuse_strategy,
            "created_at": portfolio.created_at.isoformat(),
        }
        for portfolio in portfolios
    ]
