"""Cosmetics shop: browse, buy, equip, inventory."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Item, User, UserItem
from ..schemas import BuyIn, EquipIn
from ..security import get_current_user, get_current_user_optional
from ..serializers import Serializer

router = APIRouter(prefix="/api/shop", tags=["shop"])


def owned_item_ids(db: Session, user_id: int) -> set[int]:
    rows = db.query(UserItem.item_id).filter(UserItem.user_id == user_id).all()
    return {r[0] for r in rows}


@router.get("/items")
def list_items(
    type: str | None = None,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    ser = Serializer(db)
    query = db.query(Item).filter(Item.is_active.is_(True))
    if type:
        query = query.filter(Item.type == type)
    if user is None:
        items = [i for i in query.order_by(Item.type, Item.sort_order, Item.price).all()
                 if not i.is_admin_only]
        return [ser.item(i) for i in items]

    owned = owned_item_ids(db, user.id)
    items = query.order_by(Item.type, Item.sort_order, Item.price).all()
    visible = [i for i in items if not i.is_admin_only or user.is_admin]
    return [ser.item(i, owned=i.id in owned) for i in visible]


@router.get("/inventory")
def inventory(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ser = Serializer(db)
    rows = (
        db.query(Item)
        .join(UserItem, UserItem.item_id == Item.id)
        .filter(UserItem.user_id == user.id)
        .order_by(Item.type, Item.sort_order)
        .all()
    )
    return [ser.item(i, owned=True) for i in rows]


@router.post("/buy")
def buy(payload: BuyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.key == payload.key).first()
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.is_admin_only and not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only item")

    already = (
        db.query(UserItem)
        .filter(UserItem.user_id == user.id, UserItem.item_id == item.id)
        .first()
    )
    if already:
        raise HTTPException(status_code=409, detail="You already own this")

    if user.balance < item.price:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    user.balance = round(user.balance - item.price, 2)
    db.add(UserItem(user_id=user.id, item_id=item.id))
    db.commit()
    db.refresh(user)
    return {
        "ok": True,
        "balance": round(user.balance, 2),
        "item": Serializer(db).item(item, owned=True),
    }


@router.post("/equip")
def equip(payload: EquipIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.key == payload.key).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    owns = (
        db.query(UserItem)
        .filter(UserItem.user_id == user.id, UserItem.item_id == item.id)
        .first()
    )
    if not owns and not item.is_default and not (item.is_admin_only and user.is_admin):
        raise HTTPException(status_code=403, detail="You do not own this item")

    if item.type == "frame":
        user.frame_key = item.key
    elif item.type == "font":
        user.font_key = item.key
    elif item.type == "avatar":
        user.avatar_url = item.asset_url
    elif item.type == "banner":
        user.banner_url = item.asset_url

    db.commit()
    db.refresh(user)
    return {"ok": True, "user": Serializer(db).user(user, include_private=True)}


@router.post("/unequip")
def unequip(payload: EquipIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    kind = payload.key  # "frame" or "font"
    if kind == "frame":
        user.frame_key = None
    elif kind == "font":
        user.font_key = None
    else:
        raise HTTPException(status_code=400, detail="Only frame or font can be unequipped")
    db.commit()
    return {"ok": True, "user": Serializer(db).user(user, include_private=True)}
