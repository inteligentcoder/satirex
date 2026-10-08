"""Admin tools (only reachable by admin accounts)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Item, Post, PromoCode, Transaction, User
from ..schemas import AdminUserUpdate, ItemIn, ItemUpdate, PromoCreateIn
from ..security import require_admin
from ..serializers import Serializer

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
def stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "users": db.query(func.count(User.id)).scalar() or 0,
        "posts": db.query(func.count(Post.id)).scalar() or 0,
        "items": db.query(func.count(Item.id)).scalar() or 0,
        "money_circulating": round(
            db.query(func.coalesce(func.sum(User.balance), 0.0)).scalar() or 0.0, 2
        ),
        "transactions": db.query(func.count(Transaction.id)).scalar() or 0,
    }


# ------------------------------------------------------------------ users
@router.get("/users")
def list_users(
    q: str = Query(default="", max_length=64),
    limit: int = Query(default=50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ser = Serializer(db)
    query = db.query(User)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.username.ilike(like), User.email.ilike(like)))
    users = query.order_by(User.id.desc()).limit(limit).all()
    return [ser.user(u, include_private=True) for u in users]


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.is_verified is not None:
        user.is_verified = payload.is_verified
    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    if payload.is_banned is not None:
        user.is_banned = payload.is_banned
    if payload.balance is not None:
        user.balance = round(payload.balance, 2)
    if payload.xp is not None:
        user.xp = payload.xp
    db.commit()
    db.refresh(user)
    return Serializer(db).user(user, include_private=True)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself")
    db.delete(user)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ promos
@router.get("/promo")
def list_promos(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    promos = db.query(PromoCode).order_by(PromoCode.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "code": p.code,
            "amount": p.amount,
            "max_uses": p.max_uses,
            "uses": p.uses,
            "is_active": p.is_active,
            "expires_at": p.expires_at.isoformat() if p.expires_at else None,
        }
        for p in promos
    ]


@router.post("/promo")
def create_promo(
    payload: PromoCreateIn,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    code = payload.code.strip().upper()
    if db.query(PromoCode).filter(PromoCode.code == code).first():
        raise HTTPException(status_code=409, detail="Code already exists")
    expires_at = payload.expires_at
    if expires_at is not None and expires_at.tzinfo is not None:
        from datetime import timezone

        expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
    promo = PromoCode(
        code=code,
        amount=payload.amount,
        max_uses=payload.max_uses,
        is_active=payload.is_active,
        expires_at=expires_at,
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return {"id": promo.id, "code": promo.code}


@router.delete("/promo/{promo_id}")
def delete_promo(
    promo_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    promo = db.get(PromoCode, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo not found")
    db.delete(promo)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ items
@router.get("/items")
def admin_items(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    ser = Serializer(db)
    return [ser.item(i) for i in db.query(Item).order_by(Item.type, Item.sort_order).all()]


@router.post("/items")
def create_item(
    payload: ItemIn,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(Item).filter(Item.key == payload.key).first():
        raise HTTPException(status_code=409, detail="Item key already exists")
    item = Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return Serializer(db).item(item)


@router.patch("/items/{item_id}")
def update_item(
    item_id: int,
    payload: ItemUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return Serializer(db).item(item)


@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
