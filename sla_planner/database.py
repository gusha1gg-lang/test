"""
database.py — Настройка SQLAlchemy engine и сессии.
Для смены БД достаточно изменить DATABASE_URL в .env файле.
SQLite → PostgreSQL — только смена строки подключения.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings


# Создание engine — работает и с SQLite, и с PostgreSQL
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""
    pass


def get_db():
    """Dependency для FastAPI — предоставляет сессию БД."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Создание таблиц в БД (вызывается при старте)."""
    Base.metadata.create_all(bind=engine)
