from backend.config.settings import DATABASE_URL


def get_database_url():
    """
    Returns the configured database URL.

    Later, this file will also create the
    PostgreSQL engine and database sessions.
    """

    return DATABASE_URL