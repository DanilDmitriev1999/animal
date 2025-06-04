"""
Подключение к базе данных
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager
from utils.config import settings
from models.database_models import Base
import logging

logger = logging.getLogger(__name__)

# Синхронный движок для создания таблиц
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Асинхронный движок для работы приложения
async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(async_database_url, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Dependency для получения сессии БД
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Функция создания таблиц
async def create_tables():
    """Создание таблиц в базе данных"""
    try:
        # Используем синхронный движок для создания таблиц
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

# Получение синхронной сессии для миграций и setup
def get_sync_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для проверки подключения к БД
async def check_database_connection():
    """Проверка подключения к базе данных"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            logger.info("✅ Подключение к базе данных успешно")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False 