#!/usr/bin/env python3
"""
// AICODE-NOTE: CLI для запуска SQL-скриптов через Python (psycopg2)

Команды:
  - reset  → backend/sql/00_reset.sql
  - schema → backend/sql/01_schema.sql
  - seed   → backend/sql/02_seed.sql
  - init   → reset + schema + seed

Переменные окружения (опционально):
  - DB_URL (приоритетно), например: postgresql://user:password@localhost:5432/ai_learning_db
  - DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME (если DB_URL не указан)
"""

import argparse
import os
from pathlib import Path
from typing import Iterable, List

# АICODE-NOTE: Используем psycopg2-binary для поддержки multi-statement execute()
import psycopg2  # type: ignore
from psycopg2.extensions import connection as PgConnection

try:
    # AICODE-NOTE: Поддержка .env при наличии
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # type: ignore


def build_db_url_from_env() -> str:
    """Собирает DSN для PostgreSQL из окружения либо берёт DB_URL."""
    db_url = os.getenv("DB_URL")
    if db_url:
        return db_url

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "user")
    password = os.getenv("DB_PASSWORD", "password")
    name = os.getenv("DB_NAME", "ai_learning_db")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def read_sql_file(sql_path: Path) -> str:
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL файл не найден: {sql_path}")
    return sql_path.read_text(encoding="utf-8")


def _strip_wrapping_begin_commit(sql_text: str) -> str:
    """Удаляет одиночные обёртки BEGIN/COMMIT из файла на верхнем уровне.

    Примитивная реализация: удаляем строки, которые целиком состоят из BEGIN; или COMMIT; (игнорируя пробелы и регистр).
    На текущих скриптах этого достаточно; конструкций DO $$ BEGIN ... END $$ нет.
    """
    lines = sql_text.splitlines()
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip().rstrip(";")
        upper = stripped.upper()
        if upper in {"BEGIN", "COMMIT"}:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def execute_sql_files(dsn: str, files: Iterable[Path]) -> None:
    connection: PgConnection = psycopg2.connect(dsn)
    try:
        with connection.cursor() as cursor:
            for sql_file in files:
                print(f"[DB] Executing: {sql_file}")
                raw_sql = read_sql_file(sql_file)
                sql_text = _strip_wrapping_begin_commit(raw_sql)
                try:
                    cursor.execute(sql_text)
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
                print(f"[DB] Done: {sql_file}")
    finally:
        connection.close()


def get_sql_paths(names: List[str]) -> List[Path]:
    backend_dir = Path(__file__).resolve().parents[1]
    sql_dir = backend_dir / "sql"
    mapping = {
        "reset": sql_dir / "00_reset.sql",
        "schema": sql_dir / "01_schema.sql",
        "seed": sql_dir / "02_seed.sql",
    }
    return [mapping[name] for name in names]


def main() -> None:
    # AICODE-NOTE: Загружаем переменные окружения из корня и из backend/.env, если есть
    if load_dotenv is not None:
        repo_root = Path(__file__).resolve().parents[2]
        backend_dir = Path(__file__).resolve().parents[1]
        try:
            load_dotenv(repo_root / ".env")
            load_dotenv(backend_dir / ".env")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="DB helper CLI (Python)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("reset", help="Выполнить 00_reset.sql")
    subparsers.add_parser("schema", help="Выполнить 01_schema.sql")
    subparsers.add_parser("seed", help="Выполнить 02_seed.sql")
    subparsers.add_parser("init", help="reset + schema + seed")

    args = parser.parse_args()

    dsn = build_db_url_from_env()
    print(f"[DB] DSN: {dsn}")

    if args.command == "reset":
        files = get_sql_paths(["reset"]) 
    elif args.command == "schema":
        files = get_sql_paths(["schema"]) 
    elif args.command == "seed":
        files = get_sql_paths(["seed"]) 
    elif args.command == "init":
        files = get_sql_paths(["reset", "schema", "seed"]) 
    else:
        raise ValueError(f"Неизвестная команда: {args.command}")

    execute_sql_files(dsn, files)
    print("[DB] Complete")


if __name__ == "__main__":
    main()


