"""Database engine and per-request session handling.

v1 opened a new connection in every function and only closed it on the happy
path, so any exception leaked a connection. Here one session is opened lazily
per request and always closed in a teardown hook, success or failure.
"""

from flask import Flask, current_app, g
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


def init_app(app: Flask) -> None:
    url = app.config["DATABASE_URL"]
    engine = create_engine(url)

    if url.startswith("sqlite"):
        # SQLite ignores foreign keys unless asked, every connection.
        @event.listens_for(engine, "connect")
        def _enable_sqlite_fks(dbapi_conn, _record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    app.extensions["db_engine"] = engine
    app.extensions["db_sessionmaker"] = sessionmaker(bind=engine, expire_on_commit=False)
    app.teardown_appcontext(_close_session)


def get_session() -> Session:
    if "db_session" not in g:
        g.db_session = current_app.extensions["db_sessionmaker"]()
    return g.db_session


def _close_session(_exc: BaseException | None) -> None:
    session = g.pop("db_session", None)
    if session is not None:
        session.close()  # also rolls back anything uncommitted


def create_schema(app: Flask) -> None:
    Base.metadata.create_all(app.extensions["db_engine"])


def drop_schema(app: Flask) -> None:
    Base.metadata.drop_all(app.extensions["db_engine"])
