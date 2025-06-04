"""
Настройки приложения
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
import json

class Settings(BaseSettings):
    # Основные настройки
    app_name: str = "AI Learning Platform"
    debug: bool = False

    # База данных
    database_url: str = "postgresql://user:password@localhost/ai_learning_platform"

    # Безопасность
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OpenAI по умолчанию (можно переопределить в настройках пользователя)
    default_openai_api_key: Optional[str] = None
    default_openai_model: str = "gpt-3.5-turbo"
    default_openai_base_url: str = "https://api.openai.com/v1"

    # CORS - поддержка двух форматов
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://192.168.64.1:3000,http://192.168.64.1:3001,http://192.168.1.3:3000"
    cors_origins_json: Optional[str] = None  # Для JSON формата из .env
    
    # Логирование
    log_level: str = "info"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Игнорировать дополнительные поля
    
    @property
    def cors_origins(self) -> List[str]:
        """Преобразование строки или JSON в список для CORS"""
        
        # Если есть JSON формат из переменной CORS_ORIGINS
        if self.cors_origins_json:
            try:
                parsed = json.loads(self.cors_origins_json)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Fallback к строковому формату
        base_origins = [origin.strip() for origin in self.allowed_origins.split(",")]
        
        # Добавляем дополнительные origins для разработки
        additional_origins = [
            "http://0.0.0.0:3000",
            "http://0.0.0.0:3001", 
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://192.168.64.1:5173"
        ]
        
        # Объединяем и убираем дубликаты
        all_origins = list(set(base_origins + additional_origins))
        return [origin for origin in all_origins if origin]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Проверяем переменную CORS_ORIGINS из окружения
        cors_origins_env = os.getenv('CORS_ORIGINS')
        if cors_origins_env:
            self.cors_origins_json = cors_origins_env

settings = Settings()
