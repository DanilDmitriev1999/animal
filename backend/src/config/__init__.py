from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "CHANGE_ME"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "ai_learning_db"
    db_user: str = "user"
    db_password: str = "password"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
