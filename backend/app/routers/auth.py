"""Account creation and authentication."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..economy import grant_default_items
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut
from ..security import create_access_token, get_current_user, hash_password, verify_password
from ..serializers import Serializer

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    username = payload.username.strip()
    email = payload.email.lower().strip()

    existing = (
        db.query(User)
        .filter(or_(User.username == username, User.email == email))
        .first()
    )
    if existing:
        field = "username" if existing.username == username else "email"
        raise HTTPException(status_code=409, detail=f"That {field} is already taken")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name.strip() or username,
        balance=settings.starting_balance,
    )
    db.add(user)
    db.flush()
    grant_default_items(db, user)
    db.commit()
    db.refresh(user)

    return TokenOut(
        access_token=create_access_token(user.id),
        user=Serializer(db).user(user, include_private=True),
    )


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    identifier = payload.identifier.strip()
    user = (
        db.query(User)
        .filter(or_(User.username == identifier, User.email == identifier.lower()))
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="This account is banned")

    return TokenOut(
        access_token=create_access_token(user.id),
        user=Serializer(db).user(user, include_private=True),
    )


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return Serializer(db).user(user, include_private=True)
