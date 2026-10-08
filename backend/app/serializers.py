"""ORM -> JSON helpers.

A Serializer instance caches the (small) items table so rendering a feed does
not trigger per-row lookups for frames/fonts.
"""
from __future__ import annotations

from .levels import level_progress
from .models import Item


def _iso(value):
    return value.isoformat() if value else None


class Serializer:
    def __init__(self, db):
        items = db.query(Item).all()
        self.items = {i.key: i for i in items}
        self.items_by_id = {i.id: i for i in items}

    # -- cosmetics -------------------------------------------------
    def frame(self, key: str | None):
        item = self.items.get(key) if key else None
        if not item:
            return None
        return {"key": item.key, "name": item.name, "url": item.asset_url}

    def font(self, key: str | None):
        item = self.items.get(key) if key else None
        if not item:
            return None
        return {"key": item.key, "name": item.name, "family": item.font_family}

    def item(self, item: Item, owned: bool = False) -> dict:
        return {
            "id": item.id,
            "key": item.key,
            "name": item.name,
            "type": item.type,
            "description": item.description,
            "price": item.price,
            "asset_url": item.asset_url,
            "font_family": item.font_family,
            "is_active": item.is_active,
            "is_default": item.is_default,
            "is_admin_only": item.is_admin_only,
            "sort_order": item.sort_order,
            "owned": owned,
        }

    # -- core entities --------------------------------------------
    def user(self, user, *, include_private: bool = False) -> dict:
        if user is None:
            return None
        data = {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name or user.username,
            "bio": user.bio or "",
            "avatar_url": user.avatar_url,
            "banner_url": user.banner_url,
            "frame": self.frame(user.frame_key),
            "font": self.font(user.font_key),
            "balance": round(user.balance, 2),
            "xp": user.xp,
            "level": level_progress(user),
            "is_verified": user.is_verified,
            "is_admin": user.is_admin,
            "is_banned": user.is_banned,
            "created_at": _iso(user.created_at),
        }
        if include_private:
            data["email"] = user.email
        return data

    def post(self, post, *, viewer_vote: int | None = None, comment_count: int | None = None) -> dict:
        if comment_count is None:
            comment_count = len(post.comments) if post.comments is not None else 0
        return {
            "id": post.id,
            "content": post.content,
            "media_url": post.media_url,
            "media_type": post.media_type,
            "poster_url": post.poster_url,
            "like_count": post.like_count,
            "dislike_count": post.dislike_count,
            "money_received": round(post.money_received or 0.0, 2),
            "comment_count": comment_count,
            "created_at": _iso(post.created_at),
            "author": self.user(post.author),
            "viewer_vote": viewer_vote or 0,
        }

    def comment(self, comment) -> dict:
        return {
            "id": comment.id,
            "post_id": comment.post_id,
            "content": comment.content,
            "created_at": _iso(comment.created_at),
            "author": self.user(comment.author),
        }

    def transaction(self, tx) -> dict:
        return {
            "id": tx.id,
            "sender": self.user(tx.sender),
            "receiver": self.user(tx.receiver),
            "amount": round(tx.amount, 2),
            "message": tx.message,
            "post_id": tx.post_id,
            "created_at": _iso(tx.created_at),
        }
