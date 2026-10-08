# SatireX

A satirical social platform in the spirit of Twitter/X — except the money is fake,
the status symbols are for sale, and everyone knows it. Post, tip, collect framed
avatars, buy fonts, farm XP, and argue endlessly in the comments.

> Everything here is a parody. "Money" is a fictional number in a database.
> No real payments, no real value.

## Features

- **Accounts**: register / login (JWT), editable profile, bio, avatar and banner.
- **Posts**: text + image/video, likes/dislikes, comments, per-post tipping.
- **Fake money**: balances, direct transfers, post tips, transaction history.
- **Shop & cosmetics**
  - **Profile frames** — animated GIF/AVIF rings around the avatar.
  - **Fonts** — a font-family applied to the author's posts and comments.
  - **Profile pictures** — ready-made gradient avatars.
  - **Banners** — profile header images.
  - **Admin-only items** hidden from regular users.
- **Level system** — XP for posting, commenting, getting likes and receiving money.
- **Verified icon** and **Admin icon** shown next to names.
- **Promo codes** — redeemable fake-money codes.
- **Hall of Fame / Wall of Shame** — most funded, biggest spenders, most hated, richest.
- **Admin tools** — visible only to admin accounts: user moderation (verify / admin /
  ban / edit balance & XP / delete), promo management, and shop-item management.
- **Media compression** — images are resized and converted to **AVIF**;
  videos are transcoded with **ffmpeg** (AV1 when available, H.264 fallback) with an
  AVIF poster frame.
- **Databases** — SQLite for local/testing, MariaDB for Docker, same code.
- **Docker** — compose stack with MariaDB + API + web frontend.

## Tech stack

| Layer     | Tech |
|-----------|------|
| API       | Python, FastAPI, SQLAlchemy 2, Uvicorn |
| Auth      | JWT (PyJWT) + bcrypt |
| Media     | Pillow (AVIF/WebP), ffmpeg (video) |
| Database  | SQLite (dev) / MariaDB (Docker) via SQLAlchemy |
| Frontend  | SvelteKit 3 (Svelte 5 runes) + Tailwind CSS 4, adapter-node |
| Container | Docker + Docker Compose |

## Project layout

```
.
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, routers, static /uploads
│   │   ├── config.py          # env-driven settings
│   │   ├── database.py        # engine/session (SQLite or MariaDB)
│   │   ├── models.py          # User, Post, Comment, Vote, Transaction, Item, Promo...
│   │   ├── schemas.py         # Pydantic request bodies
│   │   ├── security.py        # hashing, JWT, auth deps
│   │   ├── serializers.py     # ORM -> JSON (resolves frames/fonts/levels)
│   │   ├── economy.py         # transfers, XP, default items
│   │   ├── levels.py          # XP -> level math
│   │   ├── media.py           # image -> AVIF, video transcode
│   │   ├── seed.py            # generates assets + demo data
│   │   └── routers/           # auth, users, posts, comments, money, shop, promo, fame, admin, upload
│   ├── requirements.txt
│   ├── run.sh
│   ├── Dockerfile
│   └── uploads/               # media + generated cosmetic assets
├── frontend/
│   ├── src/
│   │   ├── lib/api.ts                 # fetch client + media URL helper
│   │   ├── lib/cosmetics.ts           # money/time/font/level helpers
│   │   ├── lib/stores/auth.svelte.ts  # auth store (runes)
│   │   ├── lib/components/            # Nav, Avatar, PostCard, Composer, LevelBar...
│   │   └── routes/                    # /, /login, /register, /u/[username], /post/[id],
│   │                                  # /shop, /fame, /admin
│   ├── Dockerfile
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
└── ADDING_ITEMS.md            # how to add new frames/fonts/avatars/banners
```

## Quick start (local, SQLite)

Two terminals.

**1. Backend**

```bash
cd backend
python -m venv .venv
./.venv/bin/pip install -r requirements.txt     # or: uv pip install --python .venv/bin/python -r requirements.txt
./run.sh                                          # http://localhost:8000  (docs at /docs)
```

On first start the API creates tables, generates the cosmetic assets (animated GIF
frames, gradient avatars/banners) and seeds demo users, posts and promo codes.

**2. Frontend**

```bash
cd frontend
pnpm install
pnpm dev                                          # http://localhost:5173
```

The frontend talks to `http://localhost:8000` by default. To point it elsewhere,
set `VITE_API_BASE` in `frontend/.env` (or set `window.__SATIREX_API_BASE__`).

Production build: `pnpm build` then `node build/index.js` (serves on port 3000).

## Docker (MariaDB)

```bash
cp .env.example .env        # optional: edit secrets
docker compose up --build
```

- Web UI: <http://localhost:3000>
- API: <http://localhost:8000> (docs at `/docs`)
- MariaDB data and uploaded media persist in named volumes (`db_data`, `uploads`).

Change `VITE_API_BASE` if the browser reaches the backend somewhere other than
`http://localhost:8000` (it is baked into the frontend build, so rebuild the
frontend image after changing it).

## Default accounts, promo codes

Seeded on first run (override with env vars `ADMIN_USERNAME`, `ADMIN_PASSWORD`,
`ADMIN_EMAIL`):

| Account | Password | Notes |
|---------|----------|-------|
| `admin` | `admin1234` | admin + verified, has the admin frame |
| `cryptobro`, `doomposter`, `memelord` | `password` | demo users |

Promo codes: `WELCOME` (+500, unlimited), `FREEMONEY` (+1000, 100 uses),
`SATIRE` (+250, 10 uses).

## Configuration (backend env vars)

| Var | Default | Purpose |
|-----|---------|---------|
| `DATABASE_URL` | `sqlite:///./databases/database.db` | SQLite or `mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4` |
| `SECRET_KEY` | `dev-secret-change-me-in-production` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_DAYS` | `7` | token lifetime |
| `CORS_ORIGINS` | `*` | comma-separated allowed origins |
| `UPLOADS_DIR` | `backend/uploads` | where media is stored/served |
| `MAX_IMAGE_DIM` | `1600` | max image dimension before AVIF encoding |
| `AVIF_QUALITY` | `60` | AVIF quality |
| `VIDEO_CODEC` | `auto` | `auto` / `av1` / `h264` |
| `VIDEO_CRF` | `30` | video quality (lower = better) |
| `MAX_UPLOAD_MB` | `50` | max upload size |
| `STARTING_BALANCE` | `1000` | new-account balance |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | admin seed |

## Media notes

- **Images** (posts, avatars, banners) are downscaled and saved as **AVIF**.
  Animated frames are saved as animated AVIF, falling back to animated WebP.
- **Videos** are transcoded with ffmpeg to MP4 (AV1 via `libaom-av1` when the
  ffmpeg build has it, otherwise H.264), plus an AVIF poster image.
- Uploaded files are served from `/uploads/...` by the API.

## Admin tools

Log in as an admin and an **Admin** link appears in the nav. The dashboard has:

- Overview stats (users, posts, items, money in circulation, transactions).
- User moderation: verified, admin, ban, edit balance/XP, delete.
- Promo code creation/listing/deletion.
- Shop item creation/listing/enable-disable/deletion (upload an asset, or paste a URL).

Per-post and per-comment **Delete** controls are also shown to admins inline.

## Adding new cosmetic items

See **[ADDING_ITEMS.md](./ADDING_ITEMS.md)** for a step-by-step guide (frames,
fonts, profile pictures, banners) both through the admin UI and through the seed
script.

## API overview

```
POST   /api/auth/register            POST /api/auth/login        GET /api/auth/me
GET    /api/users?q=                 GET  /api/users/{username}  PATCH /api/users/me
GET    /api/users/{username}/posts
GET    /api/posts?sort=recent|top|rich   POST /api/posts   GET/DELETE /api/posts/{id}
POST   /api/posts/{id}/vote          POST /api/posts/{id}/money
GET    /api/posts/{id}/comments      POST /api/posts/{id}/comments   DELETE /api/comments/{id}
POST   /api/money/send               GET  /api/money/transactions
GET    /api/shop/items               GET  /api/shop/inventory
POST   /api/shop/buy                 POST /api/shop/equip        POST /api/shop/unequip
POST   /api/promo/redeem             GET  /api/fame
POST   /api/upload                   (multipart: file, kind=avatar|banner|frame|post)
GET    /api/admin/stats              GET  /api/admin/users       PATCH/DELETE /api/admin/users/{id}
GET/POST /api/admin/promo            DELETE /api/admin/promo/{id}
GET/POST /api/admin/items            PATCH/DELETE /api/admin/items/{id}
```

Interactive docs: <http://localhost:8000/docs>.
