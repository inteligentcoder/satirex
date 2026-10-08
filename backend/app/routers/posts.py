"""Posts, votes and per-post money."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..economy import award_xp, transfer
from ..models import Comment, Post, User, Vote
from ..schemas import MoneySendIn, PostIn, VoteIn
from ..security import get_current_user, get_current_user_optional
from ..serializers import Serializer

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _viewer_votes(db: Session, viewer: User | None, post_ids: list[int]) -> dict[int, int]:
    if viewer is None or not post_ids:
        return {}
    rows = (
        db.query(Vote.post_id, Vote.value)
        .filter(Vote.user_id == viewer.id, Vote.post_id.in_(post_ids))
        .all()
    )
    return {pid: val for pid, val in rows}


def _comment_counts(db: Session, post_ids: list[int]) -> dict[int, int]:
    if not post_ids:
        return {}
    rows = (
        db.query(Comment.post_id, func.count(Comment.id))
        .filter(Comment.post_id.in_(post_ids))
        .group_by(Comment.post_id)
        .all()
    )
    return {pid: cnt for pid, cnt in rows}


def serialize_many(db: Session, posts: list[Post], viewer: User | None) -> list[dict]:
    ser = Serializer(db)
    ids = [p.id for p in posts]
    votes = _viewer_votes(db, viewer, ids)
    counts = _comment_counts(db, ids)
    return [ser.post(p, viewer_vote=votes.get(p.id), comment_count=counts.get(p.id, 0)) for p in posts]


@router.get("")
def feed(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="recent", pattern="^(recent|top|rich)$"),
    author: str | None = Query(default=None, max_length=32),
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    query = db.query(Post).join(User).filter(User.is_banned.is_(False))
    if author:
        query = query.filter(User.username == author)
    if sort == "top":
        query = query.order_by((Post.like_count - Post.dislike_count).desc(), Post.created_at.desc())
    elif sort == "rich":
        query = query.order_by(Post.money_received.desc(), Post.created_at.desc())
    else:
        query = query.order_by(Post.created_at.desc())
    posts = query.offset(offset).limit(limit).all()
    return serialize_many(db, posts, viewer)


@router.post("")
def create_post(
    payload: PostIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.content.strip() and not payload.media_url:
        raise HTTPException(status_code=400, detail="Post needs text or media")
    post = Post(
        user_id=user.id,
        content=payload.content.strip()[:2000],
        media_url=payload.media_url,
        media_type=payload.media_type,
        poster_url=payload.poster_url,
    )
    db.add(post)
    award_xp(user, settings.xp_post)
    db.commit()
    db.refresh(post)
    return Serializer(db).post(post)


@router.get("/{post_id}")
def get_post(
    post_id: int,
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return serialize_many(db, [post], viewer)[0]


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(post)
    db.commit()
    return {"ok": True}


@router.post("/{post_id}/vote")
def vote_post(
    post_id: int,
    payload: VoteIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = (
        db.query(Vote)
        .filter(Vote.user_id == user.id, Vote.post_id == post_id)
        .first()
    )
    old = existing.value if existing else 0
    new = payload.value

    if new == 0:
        if existing:
            db.delete(existing)
    elif existing:
        existing.value = new
    else:
        db.add(Vote(user_id=user.id, post_id=post_id, value=new))

    # Adjust denormalized counters.
    if old == 1:
        post.like_count = max(0, post.like_count - 1)
    elif old == -1:
        post.dislike_count = max(0, post.dislike_count - 1)
    if new == 1:
        post.like_count += 1
    elif new == -1:
        post.dislike_count += 1

    if post.user_id != user.id:
        if new == 1 and old != 1:
            award_xp(post.author, settings.xp_like_received)
        elif new == -1 and old != -1:
            award_xp(post.author, -1)

    db.commit()
    db.refresh(post)
    return Serializer(db).post(post, viewer_vote=new)


@router.post("/{post_id}/money")
def tip_post(
    post_id: int,
    payload: MoneySendIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    receiver = db.get(User, post.user_id)
    tx = transfer(db, user, receiver, payload.amount, payload.message or "Take my fake money!", post_id=post.id)
    db.commit()
    db.refresh(post)
    db.refresh(tx)
    return {"transaction": Serializer(db).transaction(tx), "post": Serializer(db).post(post)}
