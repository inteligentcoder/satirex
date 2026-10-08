"""Comments."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..economy import award_xp
from ..models import Comment, Post, User
from ..schemas import CommentIn
from ..security import get_current_user
from ..serializers import Serializer

router = APIRouter(prefix="/api", tags=["comments"])


@router.get("/posts/{post_id}/comments")
def list_comments(
    post_id: int,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if not db.get(Post, post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    ser = Serializer(db)
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [ser.comment(c) for c in comments]


@router.post("/posts/{post_id}/comments")
def add_comment(
    post_id: int,
    payload: CommentIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comment = Comment(post_id=post_id, user_id=user.id, content=payload.content.strip())
    db.add(comment)
    award_xp(user, settings.xp_comment)
    if post.user_id != user.id:
        award_xp(post.author, 1)
    db.commit()
    db.refresh(comment)
    return Serializer(db).comment(comment)


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(comment)
    db.commit()
    return {"ok": True}
