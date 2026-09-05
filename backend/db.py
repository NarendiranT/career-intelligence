from collections.abc import Generator
from contextlib import contextmanager

from pgvector.psycopg import register_vector
from sqlalchemy import event, text
from sqlmodel import Session, create_engine

from backend.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


@event.listens_for(engine, "connect")
def _register_vector(dbapi_connection, _connection_record) -> None:
    register_vector(dbapi_connection)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ensure_vector_extension() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
