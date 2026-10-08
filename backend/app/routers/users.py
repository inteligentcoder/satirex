"""User profiles and self-service profile updates."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Item, Post, User, UserItem
from ..schemas import UserUpdate
from ..security import get_current_user
from ..serializers import Serializer

router = APIRouter(prefix="/api/users", tags=["users"])


def _owned_keys(db: Session, user: User) -> set[str]:
    rows = (
        db.query(Item.key)
        .join(UserItem, UserItem.item_id == Item.id)
        .filter(UserItem.user_id == user.id)
        .all()
    )
    return {r[0] for r in rows}


@router.get("/me")
def my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ser = Serializer(db)
    data = ser.user(user, include_private=True)
    owned = _owned_keys(db, user)
    data["inventory"] = [
        ser.item(i, owned=True)
        for i in db.query(Item).filter(Item.key.in_(owned)).all()
    ] if owned else []
    return data


@router.patch("/me")
def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned = _owned_keys(db, user)

    if payload.display_name is not None:
        user.display_name = payload.display_name.strip()[:64] or user.username
    if payload.bio is not None:
        user.bio = payload.bio.strip()[:500]
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url or None
    if payload.banner_url is not None:
        user.banner_url = payload.banner_url or None

    if payload.frame_key is not None:
        if payload.frame_key == "":
            user.frame_key = None
        else:
            item = db.query(Item).filter(Item.key == payload.frame_key).first()
            if not item or item.type != "frame":
                raise HTTPException(status_code=400, detail="Unknown frame")
            if item.key not in owned and not item.is_default:
                raise HTTPException(status_code=403, detail="You do not own this frame")
            user.frame_key = item.key

    if payload.font_key is not None:
        if payload.font_key == "":
            user.font_key = None
        else:
            item = db.query(Item).filter(Item.key == payload.font_key).first()
            if not item or item.type != "font":
                raise HTTPException(status_code=400, detail="Unknown font")
            if item.key not in owned and not item.is_default:
                raise HTTPException(status_code=403, detail="You do not own this font")
            user.font_key = item.key

    db.commit()
    db.refresh(user)
    return Serializer(db).user(user, include_private=True)


@router.get("")
def search_users(
    q: str = Query(default="", max_length=64),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    ser = Serializer(db)
    query = db.query(User).filter(User.is_banned.is_(False))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.username.ilike(like), User.display_name.ilike(like)))
    users = query.order_by(User.xp.desc()).limit(limit).all()
    return [ser.user(u) for u in users]


@router.get("/{username}")
def get_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return Serializer(db).user(user)


@router.get("/{username}/posts")
def user_posts(
    username: str,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    ser = Serializer(db)
    posts = (
        db.query(Post)
        .filter(Post.user_id == user.id)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [ser.post(p) for p in posts]
