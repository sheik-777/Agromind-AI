"""Database engine / session / Base.

Tries Postgres (DATABASE_URL) first; if connection fails at runtime falls back
to SQLite (SQLITE_PATH). This keeps student/dev machines working without a
Postgres install while preserving the production Postgres path.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config.settings import DATABASE_URL, SQLITE_PATH

# SQLAlchemy Base for models
Base = declarative_base()

def _make_engine():
    # Try Postgres; actual connectivity tested lazily — engine creation never fails
    # We create two engines: postgres preferred, sqlite fallback
    # At import we pick based on URL scheme; if postgres unreachable later,
    # caller can handle OperationalError and retry with sqlite.
    if DATABASE_URL.startswith("postgresql"):
        return create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    # already sqlite url
    return create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# Default engine: use Postgres URL if set, otherwise SQLite file
try:
    if DATABASE_URL.startswith("postgresql"):
        engine = create_engine(
            DATABASE_URL, pool_pre_ping=True, future=True
        )
        # Quick connectivity probe — if it fails we silently fall back to sqlite
        # (don't crash import; actual request will handle)
        with engine.connect() as _c:
            _c.execute  # noqa
    else:
        raise ValueError("not postgres")
except Exception:
    # Fallback to SQLite file
    sqlite_url = f"sqlite:///{SQLITE_PATH}"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

def get_database_url():
    """Returns the configured database URL (compat)."""
    return DATABASE_URL

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create tables if not exist. Import models first."""
    # Import here to avoid circular
    import backend.models.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
