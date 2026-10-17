import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

DB_URL = "sqlite:///enlace.db"

engine = create_engine(
    DB_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


# SQLITE enable foregin key suppport
@event.listens_for(engine, "connect")
def configure_sqlite_connection(
    dbapi_connection: sqlite3.Connection, _connection_record: object
) -> None:
    del _connection_record
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
    finally:
        cursor.close()

SessionLocal = sessionmaker(autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()