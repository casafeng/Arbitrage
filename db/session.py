"""Database session/engine initialization."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base


def create_engine_and_session(db_url: str):
    engine = create_engine(
        db_url,
        future=True,
        echo=False,
    )

    Base.metadata.create_all(engine)

    session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    return engine, session_local
