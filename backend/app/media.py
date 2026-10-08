"""Media processing.

Images are compressed/resized and saved as AVIF (animated frames fall back to
animated WebP when the Pillow build cannot write animated AVIF).

Videos are transcoded with ffmpeg. By default we try AV1 (libaom-av1); if that
encoder is unavailable we fall back to H.264. A poster frame is extracted and
saved as AVIF.
"""
from __future__ import annotations

import io
import shutil
import subprocess
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageSequence

from .config import settings

IMAGE_FORMATS = {"JPEG", "PNG", "GIF", "WEBP", "BMP", "AVIF", "TIFF", "PPM"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v", ".mpeg", ".mpg"}

_KIND_DIRS = {
    "avatar": "avatars",
    "banner": "banners",
    "frame": "frames",
    "post": "posts",
    "media": "posts",
}


def _target_dir(kind: str) -> Path:
    sub = _KIND_DIRS.get(kind, "misc")
    path = settings.uploads_dir / sub
    path.mkdir(parents=True, exist_ok=True)
    return path


def _url_for(path: Path) -> str:
    rel = path.relative_to(settings.uploads_dir)
    return f"/uploads/{rel.as_posix()}"


def _max_dim_for(kind: str) -> int:
    if kind == "avatar":
        return settings.avatar_dim
    if kind == "banner":
        return settings.banner_dim
    return settings.max_image_dim


def _open_image(data: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        return img
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Unsupported image: {exc}") from exc


def _flatten(img: Image.Image, keep_alpha: bool) -> Image.Image:
    if keep_alpha:
        return img.convert("RGBA")
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        rgba = img.convert("RGBA")
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    return img.convert("RGB")


def _resize(img: Image.Image, max_dim: int) -> Image.Image:
    if max_dim and max(img.size) > max_dim:
        img = img.copy()
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    return img


def compress_image(data: bytes, kind: str = "post", *, keep_alpha: bool = False) -> dict:
    img = _open_image(data)
    max_dim = _max_dim_for(kind)
    animated = getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1

    frames = []
    durations = []
    if animated:
        for frame in ImageSequence.Iterator(img):
            frames.append(_resize(_flatten(frame, keep_alpha), max_dim))
            durations.append(frame.info.get("duration", img.info.get("duration", 80)))
    else:
        frames = [_resize(_flatten(img, keep_alpha), max_dim)]

    out_dir = _target_dir(kind)
    stem = uuid.uuid4().hex

    def _save(fmt: str, suffix: str, animated_ok: bool) -> Path | None:
        path = out_dir / f"{stem}{suffix}"
        try:
            if animated and animated_ok:
                frames[0].save(
                    path,
                    format=fmt,
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=img.info.get("loop", 0),
                    quality=settings.avif_quality,
                )
            else:
                save_kwargs = {"quality": settings.avif_quality}
                if fmt == "AVIF":
                    save_kwargs["speed"] = 6
                frames[0].save(path, format=fmt, **save_kwargs)
            return path
        except Exception:  # noqa: BLE001
            if path.exists():
                path.unlink(missing_ok=True)
            return None

    path = None
    if animated:
        # Animated AVIF first, then animated WebP.
        path = _save("AVIF", ".avif", animated_ok=True) or _save("WEBP", ".webp", True)
    else:
        path = _save("AVIF", ".avif", False) or _save("WEBP", ".webp", False)
    if path is None:
        # Last resort: PNG.
        path = out_dir / f"{stem}.png"
        frames[0].save(path, format="PNG")

    width, height = frames[0].size
    return {
        "url": _url_for(path),
        "media_type": "image",
        "width": width,
        "height": height,
        "animated": animated,
        "size_bytes": path.stat().st_size,
    }


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _has_encoder(name: str) -> bool:
    if not ffmpeg_available():
        return False
    try:
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=20,
        ).stdout
        return name in out
    except Exception:  # noqa: BLE001
        return False


def compress_video(src: Path, kind: str = "post") -> dict:
    if not ffmpeg_available():
        raise HTTPException(status_code=500, detail="ffmpeg is not installed on the server")

    out_dir = _target_dir(kind)
    stem = uuid.uuid4().hex
    out_path = out_dir / f"{stem}.mp4"
    max_dim = _max_dim_for(kind)
    scale = f"scale='min({max_dim},iw)':-2"

    if settings.video_codec in ("av1", "auto") and _has_encoder("libaom-av1"):
        codec_args = ["-c:v", "libaom-av1", "-crf", str(settings.video_crf), "-b:v", "0",
                      "-cpu-used", "6", "-row-mt", "1"]
    elif settings.video_codec in ("h264", "auto", "libx264"):
        codec_args = ["-c:v", "libx264", "-crf", str(settings.video_crf), "-preset", "veryfast"]
    else:
        codec_args = ["-c:v", "libx264", "-crf", str(settings.video_crf), "-preset", "veryfast"]

    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vf", scale,
        *codec_args,
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out_path.exists():
        raise HTTPException(status_code=400, detail=f"Video transcode failed: {proc.stderr[-400:]}")

    poster_url = None
    poster_path = out_dir / f"{stem}_poster.avif"
    try:
        thumb = out_dir / f"{stem}_poster.png"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(out_path), "-ss", "0", "-frames:v", "1", str(thumb)],
            capture_output=True, text=True, timeout=60,
        )
        if thumb.exists():
            with Image.open(thumb) as im:
                im = _resize(_flatten(im, False), max_dim)
                im.save(poster_path, format="AVIF", quality=settings.avif_quality)
            thumb.unlink(missing_ok=True)
            poster_url = _url_for(poster_path)
    except Exception:  # noqa: BLE001
        poster_url = None

    return {
        "url": _url_for(out_path),
        "media_type": "video",
        "poster_url": poster_url,
        "size_bytes": out_path.stat().st_size,
    }


def save_upload(upload: UploadFile, kind: str = "post") -> dict:
    data = upload.file.read()
    size = len(data)
    if size > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    if size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    suffix = Path(upload.filename or "").suffix.lower()
    content_type = (upload.content_type or "").lower()

    is_video = suffix in VIDEO_EXTS or content_type.startswith("video/")
    if is_video:
        tmp = settings.uploads_dir / f"_tmp_{uuid.uuid4().hex}{suffix or '.mp4'}"
        tmp.write_bytes(data)
        try:
            result = compress_video(tmp, kind)
        finally:
            tmp.unlink(missing_ok=True)
        result["original_bytes"] = size
        return result

    keep_alpha = kind in ("avatar", "frame")
    result = compress_image(data, kind, keep_alpha=keep_alpha)
    result["original_bytes"] = size
    return result
