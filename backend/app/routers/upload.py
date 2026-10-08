"""Media upload endpoint (compresses to AVIF / transcodes video)."""
from fastapi import APIRouter, Depends, File, Form, UploadFile

from ..media import save_upload
from ..models import User
from ..security import get_current_user

router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_KINDS = {"avatar", "banner", "frame", "post", "media"}


@router.post("")
def upload(
    file: UploadFile = File(...),
    kind: str = Form(default="post"),
    user: User = Depends(get_current_user),
):
    if kind not in ALLOWED_KINDS:
        kind = "post"
    return save_upload(file, kind)
