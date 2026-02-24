"""V1 identity portfolio service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.identity_portfolio import IdentityPortfolio


def generate_identity_portfolio(
    db: Session,
    *,
    user_id: str,
    primary_identity_id: str,
    backup_identity_id: str | None,
    anonymous_identity: str,
    tool_identity: str,
) -> IdentityPortfolio:
    if backup_identity_id and backup_identity_id == primary_identity_id:
        raise ValueError("backup_identity_id must be different from primary_identity_id")

    portfolio = IdentityPortfolio(
        user_id=user_id,
        primary_identity_id=primary_identity_id,
        backup_identity_id=backup_identity_id,
        anonymous_identity=anonymous_identity.strip(),
        tool_identity=tool_identity.strip(),
        conflict_avoidance=(
            "主身份负责公开观点，匿名身份处理高争议话题，工具身份承接方法产品，"
            "避免同一话题在不同身份重复冲突表述。"
        ),
        asset_reuse_strategy=(
            "同一观点先在主身份发布长文，再拆成匿名洞察与工具模板，实现跨身份复用。"
        ),
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def list_identity_portfolios(db: Session, *, user_id: str) -> list[IdentityPortfolio]:
    return (
        db.query(IdentityPortfolio)
        .filter(IdentityPortfolio.user_id == user_id)
        .order_by(IdentityPortfolio.created_at.desc())
        .all()
    )
