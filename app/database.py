import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class DatabaseConfigurationError(RuntimeError):
    pass


def build_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise DatabaseConfigurationError("DATABASE_URL is not configured")
    return sessionmaker(bind=build_engine(database_url), expire_on_commit=False)
