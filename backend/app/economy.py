"""Fake-money economy + XP helpers."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import Item, Transaction, User, UserItem


def award_xp(user: User, amount: int) -> None:
    user.xp = max(0, user.xp + int(amount))


def transfer(
    db: Session,
    sender: User,
    receiver: User,
    amount: float,
    message: str = "",
    post_id: int | None = None,
) -> Transaction:
    amount = round(float(amount), 2)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if sender.id == receiver.id:
        raise HTTPException(status_code=400, detail="You cannot send money to yourself")
    if sender.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    sender.balance = round(sender.balance - amount, 2)
    receiver.balance = round(receiver.balance + amount, 2)

    tx = Transaction(
        sender_id=sender.id,
        receiver_id=receiver.id,
        amount=amount,
        message=(message or "")[:255],
        post_id=post_id,
    )
    db.add(tx)

    if post_id is not None:
        from .models import Post

        post = db.get(Post, post_id)
        if post is not None and post.user_id == receiver.id:
            post.money_received = round((post.money_received or 0.0) + amount, 2)

    # Receiving a lot of money is worth XP.
    award_xp(receiver, max(1, int(amount // 10)))
    return tx


def grant_default_items(db: Session, user: User) -> None:
    defaults = db.query(Item).filter(Item.is_default.is_(True)).all()
    for item in defaults:
        exists = (
            db.query(UserItem)
            .filter(UserItem.user_id == user.id, UserItem.item_id == item.id)
            .first()
        )
        if not exists:
            db.add(UserItem(user_id=user.id, item_id=item.id))
    if user.frame_key is None:
        frame = next((i for i in defaults if i.type == "frame"), None)
        if frame:
            user.frame_key = frame.key
    if user.font_key is None:
        font = next((i for i in defaults if i.type == "font"), None)
        if font:
            user.font_key = font.key
