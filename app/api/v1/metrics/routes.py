"""V1 dashboard metrics API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.metrics import build_dashboard_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/dashboard", response_model=dict)
def get_dashboard_metrics(db: Session = Depends(get_db)) -> dict:
    return build_dashboard_metrics(db=db)
