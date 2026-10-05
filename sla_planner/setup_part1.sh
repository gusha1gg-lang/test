#!/bin/bash
# Скрипт создания проекта SLA Planner в WSL

echo "🚀 Создание структуры проекта..."

cd /opt/sla_planner

# Создаём папки
mkdir -p routers static/assets templates

# ============================================
# requirements.txt
# ============================================
cat > requirements.txt << 'ENDOFFILE'
fastapi>=0.115.0
uvicorn>=0.30.6
sqlalchemy>=2.0.35
requests>=2.32.3
pydantic>=2.10.0
pydantic-settings>=2.5.2
python-dotenv>=1.0.1
python-jose>=3.3.0
passlib>=1.7.4
ENDOFFILE

# ============================================
# .env.example
# ============================================
cat > .env.example << 'ENDOFFILE'
ZABBIX_URL=http://localhost:8080/api_jsonrpc.php
ZABBIX_USERNAME=Admin
ZABBIX_PASSWORD=zabbix
ZABBIX_SLA_NAME=Test SLA
DATABASE_URL=sqlite:///./sla_planner.db
AUTH_MODE=mock
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
ENDOFFILE

# ============================================
# config.py
# ============================================
cat > config.py << 'ENDOFFILE'
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    ZABBIX_URL: str = os.getenv("ZABBIX_URL", "http://localhost:8080/api_jsonrpc.php")
    ZABBIX_USERNAME: str = os.getenv("ZABBIX_USERNAME", "Admin")
    ZABBIX_PASSWORD: str = os.getenv("ZABBIX_PASSWORD", "zabbix")
    ZABBIX_SLA_NAME: str = os.getenv("ZABBIX_SLA_NAME", "Test SLA")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sla_planner.db")
    AUTH_MODE: str = os.getenv("AUTH_MODE", "mock")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

settings = Settings()
ENDOFFILE

# ============================================
# database.py
# ============================================
cat > database.py << 'ENDOFFILE'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
ENDOFFILE

echo "✅ Базовые файлы созданы!"
echo ""
echo "Теперь выполни:"
echo "  pip install -r requirements.txt"
echo ""
echo "После установки я дам команды для остальных файлов."
