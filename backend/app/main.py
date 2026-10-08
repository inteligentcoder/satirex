"""SatireX API — a satirical social platform with fake money and cosmetics."""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .config import settings
from .database import Base, SessionLocal, engine
from .routers import admin, auth, comments, fame, money, posts, promo, shop, upload, users
from .seed import run_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Wait for the database (MariaDB in Docker may still be starting).
    last_error: Exception | None = None
    for attempt in range(30):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            last_error = None
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2)
    if last_error is not None:
        raise RuntimeError(f"Could not connect to the database: {last_error}")

    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

_allow_credentials = settings.cors_origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(settings.uploads_dir)), name="uploads")

for module in (auth, users, posts, comments, money, shop, promo, fame, admin, upload):
    app.include_router(module.router)


@app.get("/")
def root():
    return {"name": settings.app_name, "docs": "/docs", "api": "/api/"}


@app.get("/api/")
def api_root():
    return {"ok": True, "service": settings.app_name}


@app.get("/api/health")
def health():
    return {"status": "healthy"}
