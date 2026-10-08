"""Application configuration, driven by environment variables.

Everything has a sane default so the app runs out of the box with SQLite.
For Docker/production, see docker-compose.yml and .env.example.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# backend/ directory (the parent of the app package)
BASE_DIR = Path(__file__).resolve().parent.parent


def _split_origins(raw: str):
    raw = raw.strip()
    if raw == "*" or raw == "":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "SatireX")
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_days = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7"))

        # SQLite for local/testing, MariaDB/MySQL for Docker.
        # Examples:
        #   sqlite:///./databases/database.db
        #   mysql+pymysql://satire:satire@db:3306/satire?charset=utf8mb4
        default_sqlite = f"sqlite:///{BASE_DIR / 'databases' / 'database.db'}"
        self.database_url = os.getenv("DATABASE_URL", default_sqlite)

        self.uploads_dir = Path(os.getenv("UPLOADS_DIR", str(BASE_DIR / "uploads")))
        self.cors_origins = _split_origins(os.getenv("CORS_ORIGINS", "*"))

        # Media compression.
        self.max_image_dim = int(os.getenv("MAX_IMAGE_DIM", "1600"))
        self.avatar_dim = int(os.getenv("AVATAR_DIM", "512"))
        self.banner_dim = int(os.getenv("BANNER_DIM", "1500"))
        self.avif_quality = int(os.getenv("AVIF_QUALITY", "60"))
        self.max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "50"))
        # ffmpeg video encoder: "auto" tries av1 (libaom-av1) then falls back to h264.
        self.video_codec = os.getenv("VIDEO_CODEC", "auto")
        self.video_crf = int(os.getenv("VIDEO_CRF", "30"))

        # Seeded admin account.
        self.admin_username = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_email = os.getenv("ADMIN_EMAIL", "admin@satirex.local")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "admin1234")

        # Economy knobs.
        self.starting_balance = float(os.getenv("STARTING_BALANCE", "1000"))
        self.xp_post = int(os.getenv("XP_POST", "10"))
        self.xp_comment = int(os.getenv("XP_COMMENT", "3"))
        self.xp_like_received = int(os.getenv("XP_LIKE_RECEIVED", "2"))


settings = Settings()

# Make sure runtime directories exist.
(BASE_DIR / "databases").mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
(settings.uploads_dir / "assets" / "frames").mkdir(parents=True, exist_ok=True)
(settings.uploads_dir / "assets" / "avatars").mkdir(parents=True, exist_ok=True)
(settings.uploads_dir / "assets" / "banners").mkdir(parents=True, exist_ok=True)
