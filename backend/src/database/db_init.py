#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных AI Learning Platform
Запускает SQL скрипт для создания таблиц и проверяет подключение
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path


def get_db_connection_params():
    """Получение параметров подключения к БД из переменных окружения или по умолчанию"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'ai_learning_db'),
        'user': os.getenv('DB_USER', 'user'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }


def test_connection():
    """Тестирование подключения к PostgreSQL"""
    params = get_db_connection_params()
    try:
        # Подключение без указания конкретной БД для проверки сервера
        conn = psycopg2.connect(
            host=params['host'],
            port=params['port'],
            user=params['user'],
            password=params['password'],
            database='postgres'  # подключаемся к системной БД
        )
        conn.close()
        print(f"✅ Подключение к PostgreSQL сервер успешно ({params['host']}:{params['port']})")
        return True
    except psycopg2.Error as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False


def create_database_if_not_exists():
    """Создание базы данных если она не существует"""
    params = get_db_connection_params()
    try:
        # Подключаемся к postgres для создания новой БД
        conn = psycopg2.connect(
            host=params['host'],
            port=params['port'],
            user=params['user'],
            password=params['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Проверяем существует ли БД
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (params['database'],)
        )
        
        if cursor.fetchone() is None:
            cursor.execute(f'CREATE DATABASE "{params["database"]}"')
            print(f"✅ База данных '{params['database']}' создана")
        else:
            print(f"ℹ️  База данных '{params['database']}' уже существует")
        
        cursor.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"❌ Ошибка создания базы данных: {e}")
        return False


def run_sql_script():
    """Выполнение SQL скрипта для создания таблиц"""
    params = get_db_connection_params()
    script_path = Path(__file__).parent / 'init_db.sql'
    
    if not script_path.exists():
        print(f"❌ SQL скрипт не найден: {script_path}")
        return False
    
    try:
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        cursor.execute(sql_script)
        conn.commit()
        
        cursor.close()
        conn.close()
        print("✅ SQL скрипт выполнен успешно")
        return True
    except psycopg2.Error as e:
        print(f"❌ Ошибка выполнения SQL скрипта: {e}")
        return False


def verify_tables():
    """Проверка созданных таблиц и данных"""
    params = get_db_connection_params()
    try:
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # Проверяем созданные таблицы
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """)
        tables = cursor.fetchall()
        
        print("\n📋 Созданные таблицы:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  • {table[0]}: {count} записей")
        
        # Проверяем тестовые данные
        print("\n🔍 Проверка тестовых данных:")
        
        cursor.execute("SELECT title FROM tracks")
        tracks = cursor.fetchall()
        print(f"  • Треки: {[track[0] for track in tracks]}")
        
        cursor.execute("SELECT email FROM users")
        users = cursor.fetchall()
        print(f"  • Пользователи: {[user[0] for user in users]}")
        
        cursor.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"❌ Ошибка проверки таблиц: {e}")
        return False


def main():
    """Основная функция инициализации БД"""
    print("🚀 Инициализация базы данных AI Learning Platform")
    print("=" * 50)
    
    # Шаг 1: Проверка подключения
    if not test_connection():
        print("\n💡 Убедитесь что Docker контейнер с PostgreSQL запущен:")
        print("   make up  (или docker-compose up -d)")
        sys.exit(1)
    
    # Шаг 2: Создание БД
    if not create_database_if_not_exists():
        sys.exit(1)
    
    # Шаг 3: Выполнение SQL скрипта
    if not run_sql_script():
        sys.exit(1)
    
    # Шаг 4: Проверка результата
    if not verify_tables():
        sys.exit(1)
    
    print("\n🎉 Инициализация завершена успешно!")
    print("\n📝 Тестовый пользователь создан:")
    print("   Email: test@example.com")
    print("   Password: test123")


if __name__ == "__main__":
    main() 