"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

USERNAME_PATTERN = r"^[A-Za-z0-9_]{3,32}$"


# ---------------------------------------------------------------- auth
class RegisterIn(BaseModel):
    username: str = Field(pattern=USERNAME_PATTERN)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(default="", max_length=64)


class LoginIn(BaseModel):
    identifier: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ---------------------------------------------------------------- users
class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=64)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=512)
    banner_url: str | None = Field(default=None, max_length=512)
    frame_key: str | None = Field(default=None, max_length=64)
    font_key: str | None = Field(default=None, max_length=64)


# ---------------------------------------------------------------- posts
class PostIn(BaseModel):
    content: str = Field(default="", max_length=2000)
    media_url: str | None = Field(default=None, max_length=512)
    media_type: str | None = Field(default=None, max_length=16)
    poster_url: str | None = Field(default=None, max_length=512)


class CommentIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class VoteIn(BaseModel):
    value: int = Field(ge=-1, le=1)


# ---------------------------------------------------------------- money
class MoneySendIn(BaseModel):
    receiver_username: str = Field(pattern=USERNAME_PATTERN)
    amount: float = Field(gt=0, le=1_000_000)
    message: str = Field(default="", max_length=255)
    post_id: int | None = None


# ---------------------------------------------------------------- shop
class BuyIn(BaseModel):
    key: str = Field(max_length=64)


class EquipIn(BaseModel):
    key: str = Field(max_length=64)


# ---------------------------------------------------------------- promo
class PromoRedeemIn(BaseModel):
    code: str = Field(min_length=1, max_length=64)


class PromoCreateIn(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    amount: float = Field(ge=0)
    max_uses: int = Field(default=0, ge=0)
    is_active: bool = True
    expires_at: datetime | None = None


# ---------------------------------------------------------------- admin
class AdminUserUpdate(BaseModel):
    is_verified: bool | None = None
    is_admin: bool | None = None
    is_banned: bool | None = None
    balance: float | None = None
    xp: int | None = None


class ItemIn(BaseModel):
    key: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_\-]+$")
    name: str = Field(min_length=1, max_length=80)
    type: str = Field(pattern=r"^(frame|font|avatar|banner)$")
    description: str = Field(default="", max_length=500)
    price: float = Field(default=0.0, ge=0)
    asset_url: str | None = Field(default=None, max_length=512)
    font_family: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    is_default: bool = False
    is_admin_only: bool = False
    sort_order: int = 0


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=80)
    type: str | None = Field(default=None, pattern=r"^(frame|font|avatar|banner)$")
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, ge=0)
    asset_url: str | None = Field(default=None, max_length=512)
    font_family: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_default: bool | None = None
    is_admin_only: bool | None = None
    sort_order: int | None = None


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
