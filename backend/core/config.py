"""
FILE: core/config.py  — FINAL VERSION
Replace your existing backend/core/config.py with this.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # ── Groq (LLM) ────────────────────────────────────────
    GROQ_API_KEY: str
    GROQ_PRIMARY_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FAST_MODEL: str    = "llama-3.1-8b-instant"

    # ── Supabase (Auth + DB) ──────────────────────────────
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # ── OpenFDA (Drug safety) ─────────────────────────────
    OPENFDA_API_KEY: Optional[str] = ""

    # ── WHO ICD-11 (Disease classification) ──────────────
    WHO_ICD_CLIENT_ID: Optional[str]     = ""
    WHO_ICD_CLIENT_SECRET: Optional[str] = ""

    # ── IoMT (plug in when keys arrive) ──────────────────
    IOMT_API_KEY: Optional[str] = ""
    IOMT_API_URL: Optional[str] = ""

    # ── App ───────────────────────────────────────────────
    APP_ENV: str    = "development"
    SECRET_KEY: str = "changeme_in_production"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"
        extra    = "ignore"

    def get_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def openfda_enabled(self) -> bool:
        return bool(self.OPENFDA_API_KEY)

    @property
    def who_icd_enabled(self) -> bool:
        return bool(self.WHO_ICD_CLIENT_ID and self.WHO_ICD_CLIENT_SECRET)

    @property
    def iomt_enabled(self) -> bool:
        return bool(self.IOMT_API_KEY and self.IOMT_API_URL)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# =============================================================
# FILE: .env.example  — FINAL VERSION
# Copy this to .env and fill in your real values
# =============================================================

ENV_EXAMPLE = """
# ── Groq (LLM) ────────────────────────────────────────────
GROQ_API_KEY=gsk_your_groq_key_here

# ── Supabase ──────────────────────────────────────────────
SUPABASE_URL=https://eqrfweyembuqrlvpagar.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# ── OpenFDA — get free key at open.fda.gov/apis/authentication
OPENFDA_API_KEY=your_openfda_key_here

# ── WHO ICD-11 — already obtained ─────────────────────────
# WHO ICD-11
WHO_ICD_CLIENT_ID=your_who_icd_client_id
WHO_ICD_CLIENT_SECRET=your_who_icd_client_secret
# ── IoMT (leave blank until keys arrive in 4 days) ────────
IOMT_API_KEY=
IOMT_API_URL=

# ── App ───────────────────────────────────────────────────
APP_ENV=development
SECRET_KEY=healthbot_secret_change_in_production
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
"""
