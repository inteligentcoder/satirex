"""Direct fake-money transfers and transaction history."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..economy import transfer
from ..models import Transaction, User
from ..schemas import MoneySendIn
from ..security import get_current_user
from ..serializers import Serializer

router = APIRouter(prefix="/api/money", tags=["money"])


@router.post("/send")
def send_money(
    payload: MoneySendIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    receiver = db.query(User).filter(User.username == payload.receiver_username).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    tx = transfer(db, user, receiver, payload.amount, payload.message)
    db.commit()
    db.refresh(tx)
    ser = Serializer(db)
    return {"transaction": ser.transaction(tx), "balance": round(user.balance, 2)}


@router.get("/transactions")
def transactions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ser = Serializer(db)
    txs = (
        db.query(Transaction)
        .filter(or_(Transaction.sender_id == user.id, Transaction.receiver_id == user.id))
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [ser.transaction(t) for t in txs]
