"""
Конфигурация подключения к базе данных AI Learning Platform
"""

import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


# Базовый класс для моделей SQLAlchemy
Base = declarative_base()


def get_database_url():
    """Формирование строки подключения к БД"""
    db_user = os.getenv('DB_USER', 'user')
    db_password = os.getenv('DB_PASSWORD', 'password')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'ai_learning_db')
    
    # Экранирование специальных символов в пароле
    db_password_escaped = quote_plus(db_password)
    
    return f"postgresql://{db_user}:{db_password_escaped}@{db_host}:{db_port}/{db_name}"


# Создание движка SQLAlchemy
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=300,    # Переподключение каждые 5 минут
    echo=False           # Логирование SQL запросов (включать для отладки)
)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Получение сессии БД (dependency для FastAPI)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Проверка подключения к БД"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return False


if __name__ == "__main__":
    # Тест подключения при запуске файла
    if test_connection():
        print("✅ Подключение к БД успешно")
        print(f"URL: {get_database_url()}")
    else:
        print("❌ Ошибка подключения к БД") 