"""Hall of Fame / Wall of Shame leaderboards."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Post, Transaction, User
from ..serializers import Serializer

router = APIRouter(prefix="/api/fame", tags=["fame"])


def _users_by_ids(db: Session, ids: list[int]) -> dict[int, User]:
    if not ids:
        return {}
    return {u.id: u for u in db.query(User).filter(User.id.in_(ids)).all()}


@router.get("")
def hall_of_fame(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    ser = Serializer(db)

    # Most fake-money received (the beloved).
    received = (
        db.query(Transaction.receiver_id, func.sum(Transaction.amount).label("total"))
        .group_by(Transaction.receiver_id)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
        .all()
    )
    # Biggest spenders.
    sent = (
        db.query(Transaction.sender_id, func.sum(Transaction.amount).label("total"))
        .group_by(Transaction.sender_id)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
        .all()
    )
    # Most hated: total dislikes across their posts.
    hated = (
        db.query(Post.user_id, func.sum(Post.dislike_count).label("total"))
        .group_by(Post.user_id)
        .order_by(func.sum(Post.dislike_count).desc())
        .limit(limit)
        .all()
    )
    hated = [(uid, total) for uid, total in hated if total and total > 0]

    ids = {i for i, _ in received} | {i for i, _ in sent} | {i for i, _ in hated}
    users = _users_by_ids(db, list(ids))

    def pack(rows):
        out = []
        for uid, total in rows:
            u = users.get(uid)
            if u:
                out.append({"user": ser.user(u), "total": round(float(total or 0), 2)})
        return out

    richest = db.query(User).filter(User.is_banned.is_(False)).order_by(User.balance.desc()).limit(limit).all()

    return {
        "most_funded": pack(received),
        "biggest_spenders": pack(sent),
        "most_hated": pack(hated),
        "richest": [{"user": ser.user(u), "total": round(u.balance, 2)} for u in richest],
    }
