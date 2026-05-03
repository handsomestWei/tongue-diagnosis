"""数据库引擎与会话工厂。"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.config import Settings, get_settings


def make_engine(database_url: str):
    # SQLite 需要 check_same_thread=False 供 FastAPI 多线程
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(
        database_url,
        connect_args=connect_args,
        echo=False,
        pool_pre_ping=True,
    )


_settings: Settings | None = None
_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def configure_engine(settings: Settings | None = None) -> None:
    global _settings, _engine, _SessionLocal
    from db.sqlite_util import ensure_sqlite_dirs

    _settings = settings or get_settings()
    ensure_sqlite_dirs(_settings.database_url)
    _engine = make_engine(_settings.database_url)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_engine():
    if _engine is None:
        configure_engine()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    if _SessionLocal is None:
        configure_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
