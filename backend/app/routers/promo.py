"""Promo code redemption."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PromoCode, PromoRedemption, User
from ..schemas import PromoRedeemIn
from ..security import get_current_user

router = APIRouter(prefix="/api/promo", tags=["promo"])


@router.post("/redeem")
def redeem(
    payload: PromoRedeemIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    code = payload.code.strip().upper()
    promo = db.query(PromoCode).filter(PromoCode.code == code).first()
    if not promo or not promo.is_active:
        raise HTTPException(status_code=404, detail="Invalid promo code")
    if promo.expires_at and promo.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This promo code has expired")
    if promo.max_uses and promo.uses >= promo.max_uses:
        raise HTTPException(status_code=400, detail="This promo code is used up")

    already = (
        db.query(PromoRedemption)
        .filter(PromoRedemption.promo_id == promo.id, PromoRedemption.user_id == user.id)
        .first()
    )
    if already:
        raise HTTPException(status_code=409, detail="You already redeemed this code")

    user.balance = round(user.balance + promo.amount, 2)
    promo.uses += 1
    db.add(PromoRedemption(promo_id=promo.id, user_id=user.id, amount=promo.amount))
    db.commit()
    return {"ok": True, "amount": promo.amount, "balance": round(user.balance, 2)}
