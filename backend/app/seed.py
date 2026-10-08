"""Seed cosmetics assets + demo data.

Runs on startup (idempotent). Generates real animated GIF profile frames plus
AVIF avatars/banners with Pillow, then inserts shop items, an admin account,
some demo users/posts and promo codes.
"""
from __future__ import annotations

import colorsys
import math
from pathlib import Path

from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from .config import settings
from .economy import grant_default_items
from .models import Item, Post, PromoCode, Transaction, User, Vote
from .security import hash_password

ASSETS = settings.uploads_dir / "assets"
FRAMES = ASSETS / "frames"
AVATARS = ASSETS / "avatars"
BANNERS = ASSETS / "banners"


def _rgba(hex_color: str, alpha: int = 255):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def _to_gif_frames(frames: list[Image.Image]) -> list[Image.Image]:
    """Convert RGBA frames to a palette with index 255 as transparency."""
    out = []
    for frame in frames:
        alpha = frame.getchannel("A")
        pal = frame.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255)
        mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
        pal.paste(255, mask)
        out.append(pal)
    return out


def _draw_ring(size: int, radius_ratio: float, width: int, color, start: float, extent: float):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = size / 2 * radius_ratio
    box = [size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r]
    draw.arc(box, start=start, end=start + extent, fill=color, width=width)
    return img


def make_frame_gif(path: Path, color_a: str, color_b: str, *, frames: int = 16, rainbow: bool = False):
    size = 256
    rings = []
    for i in range(frames):
        t = i / frames
        angle = 360 * t
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        if rainbow:
            hue = t
            rgb = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.85, 1.0))
            c_a = rgb + (255,)
            rgb2 = tuple(int(c * 255) for c in colorsys.hsv_to_rgb((hue + 0.5) % 1, 0.9, 1.0))
            c_b = rgb2 + (255,)
        else:
            c_a = _rgba(color_a)
            c_b = _rgba(color_b)

        # Two complete rings that wrap the avatar (radii as a fraction of the
        # half-size so they always sit inside the canvas and hug the circle).
        outer_ratio, outer_w = 0.92, 10
        inner_ratio, inner_w = 0.82, 4

        r_outer = size / 2 * outer_ratio
        r_inner = size / 2 * inner_ratio
        draw.ellipse(
            [size / 2 - r_outer, size / 2 - r_outer, size / 2 + r_outer, size / 2 + r_outer],
            outline=c_a, width=outer_w,
        )
        draw.ellipse(
            [size / 2 - r_inner, size / 2 - r_inner, size / 2 + r_inner, size / 2 + r_inner],
            outline=c_b, width=inner_w,
        )

        # Rotating highlight on the outer ring.
        img.alpha_composite(_draw_ring(size, outer_ratio, outer_w, c_b, angle, 80))

        # Pulsing badge sitting on the ring band, bottom-right.
        pulse = 5 + 4 * (1 + math.sin(t * math.tau)) / 2
        d = outer_ratio * (size / 2) / math.sqrt(2) * 0.98
        cx, cy = size / 2 + d, size / 2 + d
        draw.ellipse([cx - pulse, cy - pulse, cx + pulse, cy + pulse], fill=c_b)

        rings.append(img)

    pal_frames = _to_gif_frames(rings)
    path.parent.mkdir(parents=True, exist_ok=True)
    pal_frames[0].save(
        path,
        format="GIF",
        save_all=True,
        append_images=pal_frames[1:],
        duration=90,
        loop=0,
        transparency=255,
        disposal=2,
        optimize=False,
    )


def make_gradient(path: Path, c1: str, c2: str, size=(1500, 500)):
    w, h = size
    base = Image.new("RGB", (w, h))
    px = base.load()
    a = _rgba(c1)[:3]
    b = _rgba(c2)[:3]
    for x in range(w):
        t = x / max(w - 1, 1)
        for y in range(h):
            ty = y / max(h - 1, 1)
            tt = min(1.0, t * 0.7 + ty * 0.3)
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * tt) for i in range(3))
    path.parent.mkdir(parents=True, exist_ok=True)
    base.save(path, format="AVIF", quality=settings.avif_quality, speed=6)


def make_avatar(path: Path, c1: str, c2: str, size=512):
    img = Image.new("RGB", (size, size))
    px = img.load()
    a = _rgba(c1)[:3]
    b = _rgba(c2)[:3]
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path, format="AVIF", quality=settings.avif_quality, speed=6)


def generate_assets() -> None:
    frames = [
        ("classic", "#9aa4b2", "#e2e8f0", False),
        ("gold", "#ffb300", "#fff3b0", False),
        ("neon", "#00ffc8", "#ff00d4", False),
        ("fire", "#ff3c00", "#ffd000", False),
        ("rainbow", "#ff0000", "#00ff00", True),
        ("admin", "#7b2ff7", "#ffd700", False),
    ]
    for key, c1, c2, rainbow in frames:
        path = FRAMES / f"{key}.gif"
        if not path.exists():
            make_frame_gif(path, c1, c2, rainbow=rainbow)

    banners = {
        "banner_sunset": ("#ff512f", "#dd2476"),
        "banner_ocean": ("#2193b0", "#6dd5ed"),
        "banner_forest": ("#134e5e", "#71b280"),
    }
    for key, (c1, c2) in banners.items():
        path = BANNERS / f"{key}.avif"
        if not path.exists():
            make_gradient(path, c1, c2)

    avatars = {
        "avatar_ice": ("#74ebd5", "#9face6"),
        "avatar_candy": ("#ff9a9e", "#fad0c4"),
        "avatar_lime": ("#a8e063", "#56ab2f"),
    }
    for key, (c1, c2) in avatars.items():
        path = AVATARS / f"{key}.avif"
        if not path.exists():
            make_avatar(path, c1, c2)


def _url(path: Path) -> str:
    return f"/uploads/{path.relative_to(settings.uploads_dir).as_posix()}"


def ensure_item(db: Session, key: str, **kwargs) -> Item:
    item = db.query(Item).filter(Item.key == key).first()
    if item:
        return item
    item = Item(key=key, **kwargs)
    db.add(item)
    db.flush()
    return item


def seed_items(db: Session) -> None:
    # Frames
    ensure_item(db, "classic", name="Classic Ring", type="frame", price=0, is_default=True,
                sort_order=0, asset_url=_url(FRAMES / "classic.gif"),
                description="The humble starter ring. Free forever.")
    ensure_item(db, "gold", name="Gold Frame", type="frame", price=500, sort_order=1,
                asset_url=_url(FRAMES / "gold.gif"), description="Flex your fake wealth.")
    ensure_item(db, "neon", name="Neon Pulse", type="frame", price=800, sort_order=2,
                asset_url=_url(FRAMES / "neon.gif"), description="Cyberpunk energy.")
    ensure_item(db, "fire", name="On Fire", type="frame", price=1200, sort_order=3,
                asset_url=_url(FRAMES / "fire.gif"), description="For when your takes are hot.")
    ensure_item(db, "rainbow", name="Rainbow", type="frame", price=1500, sort_order=4,
                asset_url=_url(FRAMES / "rainbow.gif"), description="Ride the rainbow.")
    ensure_item(db, "admin", name="Admin Aura", type="frame", price=0, sort_order=99,
                is_admin_only=True, asset_url=_url(FRAMES / "admin.gif"),
                description="Staff only. Do not distribute.")

    # Fonts
    ensure_item(db, "font_system", name="System Default", type="font", price=0, is_default=True,
                sort_order=0, font_family="system-ui, -apple-system, 'Segoe UI', sans-serif")
    ensure_item(db, "font_serif", name="Elegant Serif", type="font", price=300, sort_order=1,
                font_family="Georgia, 'Times New Roman', serif", description="Classy posting.")
    ensure_item(db, "font_mono", name="Terminal Mono", type="font", price=400, sort_order=2,
                font_family="'Courier New', ui-monospace, monospace", description="Hacker vibes.")
    ensure_item(db, "font_comic", name="Comic Chaos", type="font", price=600, sort_order=3,
                font_family="'Comic Sans MS', 'Comic Neue', cursive", description="Chaotic good.")
    ensure_item(db, "font_impact", name="Impact Meme", type="font", price=700, sort_order=4,
                font_family="Impact, 'Arial Black', sans-serif", description="Top text, bottom text.")

    # Avatars
    ensure_item(db, "avatar_ice", name="Ice Gradient", type="avatar", price=250, sort_order=1,
                asset_url=_url(AVATARS / "avatar_ice.avif"))
    ensure_item(db, "avatar_candy", name="Candy Gradient", type="avatar", price=250, sort_order=2,
                asset_url=_url(AVATARS / "avatar_candy.avif"))
    ensure_item(db, "avatar_lime", name="Lime Gradient", type="avatar", price=250, sort_order=3,
                asset_url=_url(AVATARS / "avatar_lime.avif"))

    # Banners
    ensure_item(db, "banner_sunset", name="Sunset Banner", type="banner", price=350, sort_order=1,
                asset_url=_url(BANNERS / "banner_sunset.avif"))
    ensure_item(db, "banner_ocean", name="Ocean Banner", type="banner", price=350, sort_order=2,
                asset_url=_url(BANNERS / "banner_ocean.avif"))
    ensure_item(db, "banner_forest", name="Forest Banner", type="banner", price=350, sort_order=3,
                asset_url=_url(BANNERS / "banner_forest.avif"))


def _user(db: Session, username: str, password: str, **kwargs) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user:
        return user
    user = User(
        username=username,
        email=kwargs.pop("email", f"{username}@satirex.local"),
        password_hash=hash_password(password),
        display_name=kwargs.pop("display_name", username),
        balance=kwargs.pop("balance", settings.starting_balance),
        **kwargs,
    )
    db.add(user)
    db.flush()
    grant_default_items(db, user)
    return user


def seed_demo(db: Session) -> None:
    admin = _user(db, settings.admin_username, settings.admin_password,
                  email=settings.admin_email, display_name="The Management",
                  balance=999999, xp=10000, is_admin=True, is_verified=True)
    admin.frame_key = "admin"

    bro = _user(db, "cryptobro", "password", display_name="Crypto Bro", balance=4200, xp=520,
                bio="Not financial advice. Definitely financial advice.",
                is_verified=True, frame_key="gold", avatar_url=_url(AVATARS / "avatar_ice.avif"))
    doom = _user(db, "doomposter", "password", display_name="Doom Poster", balance=800, xp=300,
                 bio="Everything is a bubble. Including this site.")
    meme = _user(db, "memelord", "password", display_name="Meme Lord", balance=1500, xp=1200,
                 bio="Certified shitposter.", frame_key="fire", font_key="font_impact",
                 banner_url=_url(BANNERS / "banner_sunset.avif"), avatar_url=_url(AVATARS / "avatar_candy.avif"))

    if db.query(Post).count() == 0:
        posts = [
            Post(user_id=bro.id, content="Just sold my kidney for fake internet money. Bullish.",
                 like_count=12, dislike_count=3, money_received=1500),
            Post(user_id=meme.id, content="They said I could be anything, so I became a verified icon.",
                 like_count=44, dislike_count=1, money_received=2100),
            Post(user_id=doom.id, content="This whole platform is a ponzi scheme and I love it.",
                 like_count=5, dislike_count=30, money_received=50),
            Post(user_id=bro.id, content="Tip me and I will say something profound. Probably.",
                 like_count=8, dislike_count=2, money_received=700),
        ]
        db.add_all(posts)
        db.flush()
        db.add_all([
            Transaction(sender_id=meme.id, receiver_id=bro.id, amount=1500,
                        message="For the kidney, king.", post_id=None),
            Transaction(sender_id=bro.id, receiver_id=doom.id, amount=50,
                        message="Here, buy a cope.", post_id=None),
            Transaction(sender_id=admin.id, receiver_id=meme.id, amount=2100,
                        message="Official platform subsidy.", post_id=None),
        ])
        # Link some transactions to posts for the per-post totals.
        db.add_all([
            Transaction(sender_id=meme.id, receiver_id=bro.id, amount=700,
                        message="It was profound enough.", post_id=posts[3].id),
        ])

    if db.query(PromoCode).count() == 0:
        db.add_all([
            PromoCode(code="WELCOME", amount=500, max_uses=0, is_active=True),
            PromoCode(code="FREEMONEY", amount=1000, max_uses=100, is_active=True),
            PromoCode(code="SATIRE", amount=250, max_uses=10, is_active=True),
        ])


def run_seed(db: Session) -> None:
    generate_assets()
    seed_items(db)
    seed_demo(db)
    db.commit()
