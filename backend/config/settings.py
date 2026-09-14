# ======================================
# AgroMind Project Information
# ======================================

PROJECT_NAME = "AgroMind API"

VERSION = "1.0.0"

DESCRIPTION = "AI Powered Precision Agriculture Platform"

DEBUG = True


# ======================================
# Database Configuration
# ======================================

# Use DATABASE_URL env if provided; fallback to local SQLite for student/dev
# Postgres example: postgresql://user:pass@localhost:5432/agromind
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://username:password@localhost:5432/agromind",
)

# SQLite fallback path (auto-used when Postgres unreachable)
SQLITE_PATH = os.environ.get("SQLITE_PATH", "backend/agromind.db")

# ======================================
# Auth / JWT
# ======================================

# In production set AGROMIND_SECRET_KEY env to a long random value
SECRET_KEY = os.environ.get("AGROMIND_SECRET_KEY", "agromind-dev-secret-change-in-production-32chars+")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days

# ======================================
# Weather API (Open-Meteo)
# ======================================

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
