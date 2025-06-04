"""
AI Learning Platform - FastAPI Backend
Веб-сервис для обучения определенным навыкам с AI
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import List, Dict, Any
import json
import os
from datetime import datetime

from models.database import create_tables, get_db, check_database_connection
from routers import auth, tracks, chat, ai_service
from services.chat_service import chat_manager
from utils.config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц при запуске
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск
    try:
        await create_tables()
        logger.info("Database tables created")
        
        # Проверяем подключение к БД
        await check_database_connection()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        
    yield
    # Завершение
    logger.info("Application shutdown")

# Создание FastAPI приложения
app = FastAPI(
    title="AI Learning Platform API",
    description="Веб-сервис для обучения с AI - Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS настройки для работы с отдельным frontend
cors_origins = [
    "http://localhost:3000",  # Vite dev server
    "http://localhost:3001",  # Альтернативный порт Vite (когда 3000 занят)
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://192.168.1.3:3000",  # IP адрес для локальной сети
    "http://192.168.1.3:3001",  # IP адрес для локальной сети (альтернативный порт)
    "http://192.168.64.1:3000",  # Дополнительный IP для локальной сети
    "http://192.168.64.1:3001", # Дополнительный IP для локальной сети (альтернативный порт)
    "http://localhost:5173",  # Альтернативный порт Vite
    "http://127.0.0.1:5173",
    "http://192.168.1.3:5173",
    "http://192.168.64.1:5173",
    *settings.cors_origins     # Дополнительные origins из настроек
]

# Логируем CORS настройки для отладки
logger.info(f"🌐 Configured CORS origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(tracks.router, prefix="/api/tracks", tags=["learning_tracks"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(ai_service.router, prefix="/api/ai", tags=["ai_service"])

# API информация
@app.get("/api")
async def api_info():
    """Информация об API"""
    return {
        "message": "AI Learning Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "frontend": "http://localhost:3000"
    }

# Проверка здоровья API
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ai-learning-platform"}

# WebSocket для чата с поддержкой chat_id
@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint для чата планирования курса с поддержкой chat_id"""
    await chat_manager.connect(websocket, session_id)
    logger.info(f"WebSocket connected for session: {session_id}")
    
    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Извлекаем данные сообщения
            user_message = message_data.get("message", "")
            user_id = message_data.get("user_id", "")
            message_type = message_data.get("type", "text")
            chat_id = message_data.get("chat_id")  # Новое поле для поддержки chat_id
            
            # Логируем полученное сообщение
            logger.info(f"Received message in session {session_id}, chat_id: {chat_id}, user: {user_id}, type: {message_type}")
            
            # Получаем сессию БД
            db_gen = get_db()
            db = await db_gen.__anext__()
            
            try:
                # Специальное сообщение для восстановления истории при подключении
                if message_type == "restore_chat":
                    result = await chat_manager.restore_existing_chat_if_any(
                        session_id=session_id,
                        user_id=user_id,
                        db=db
                    )
                    
                    response = {
                        "type": "chat_restored",
                        "session_id": session_id,
                        "success": result["success"],
                        "has_existing_chat": result["has_existing_chat"],
                        "chat_id": result.get("chat_id"),
                        "chat_info": result.get("chat_info"),
                        "history": result.get("history", []),
                        "message_count": result.get("message_count", 0),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(response))
                    logger.info(f"Restored chat for session {session_id}: {result['has_existing_chat']} existing, {result.get('message_count', 0)} messages")
                    continue
            
                # Проверяем обязательные поля для обычных сообщений
                if not user_message.strip():
                    error_response = {
                        "type": "error",
                        "message": "Сообщение не может быть пустым",
                        "session_id": session_id,
                        "chat_id": chat_id,
                        "timestamp": None
                    }
                    await websocket.send_text(json.dumps(error_response))
                    continue
                
                if not user_id:
                    error_response = {
                        "type": "error",
                        "message": "Не указан пользователь",
                        "session_id": session_id,
                        "chat_id": chat_id,
                        "timestamp": None
                    }
                    await websocket.send_text(json.dumps(error_response))
                    continue

                # Обрабатываем обычное сообщение через AI с сохранением в БД
                await chat_manager.process_message(
                    session_id=session_id,
                    message=user_message,
                    user_id=user_id,
                    db=db,
                    message_type=message_type,
                    chat_id=chat_id
                )
                
                logger.info(f"Processed message for session {session_id}, chat_id: {chat_id}")
                
            except Exception as e:
                logger.error(f"Error processing message in session {session_id}: {str(e)}")
                
                # Отправляем сообщение об ошибке
                error_response = {
                    "type": "error",
                    "message": f"🚫 Произошла ошибка при обработке сообщения: {str(e)}",
                    "session_id": session_id,
                    "chat_id": chat_id,
                    "timestamp": None
                }
                await websocket.send_text(json.dumps(error_response))
                
            finally:
                # Закрываем сессию БД
                await db.close()

    except WebSocketDisconnect:
        chat_manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON received in session {session_id}")
        try:
            error_response = {
                "type": "error",
                "message": "🚫 Получены некорректные данные",
                "session_id": session_id,
                "timestamp": None
            }
            await websocket.send_text(json.dumps(error_response))
        except:
            pass
    except Exception as e:
        logger.error(f"WebSocket error in session {session_id}: {str(e)}")
        try:
            error_response = {
                "type": "error",
                "message": f"🚫 Произошла ошибка соединения: {str(e)}",
                "session_id": session_id,
                "timestamp": None
            }
            await websocket.send_text(json.dumps(error_response))
        except:
            pass
        finally:
            await websocket.close()

# Дополнительный WebSocket endpoint для переключения чатов
@app.websocket("/ws/chat/{session_id}/switch")
async def websocket_switch_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint для переключения между чатами и восстановления истории"""
    await chat_manager.connect(websocket, f"{session_id}_switch")
    logger.info(f"WebSocket switch connected for session: {session_id}")
    
    try:
        while True:
            # Получаем команду переключения
            data = await websocket.receive_text()
            command_data = json.loads(data)
            
            command_type = command_data.get("command", "")
            user_id = command_data.get("user_id", "")
            
            # Получаем сессию БД
            db_gen = get_db()
            db = await db_gen.__anext__()
            
            try:
                if command_type == "switch_chat":
                    # Переключение на конкретный чат
                    chat_id = command_data.get("chat_id")
                    if chat_id:
                        result = await chat_manager.switch_to_chat(
                            session_id=session_id,
                            chat_id=chat_id,
                            user_id=user_id,
                            db=db
                        )
                        
                        response = {
                            "type": "chat_switched",
                            "session_id": session_id,
                            "chat_id": chat_id,
                            "success": result["success"],
                            "chat_info": result.get("chat_info", {}),
                            "history": result.get("history", []),
                            "message_count": result.get("message_count", 0)
                        }
                        
                        await websocket.send_text(json.dumps(response))
                        
                elif command_type == "get_user_chats":
                    # Получение всех чатов пользователя
                    user_chats = await chat_manager.get_all_user_chats(user_id, session_id, db)
                    
                    response = {
                        "type": "user_chats",
                        "session_id": session_id,
                        "chats": user_chats
                    }
                    
                    await websocket.send_text(json.dumps(response))
                    
                elif command_type == "restore_history":
                    # Восстановление истории конкретного чата
                    chat_id = command_data.get("chat_id")
                    if chat_id:
                        history = await chat_manager.restore_chat_history(
                            session_id=session_id,
                            chat_id=chat_id,
                            user_id=user_id,
                            db=db
                        )
                        
                        response = {
                            "type": "history_restored",
                            "session_id": session_id,
                            "chat_id": chat_id,
                            "history": history,
                            "message_count": len(history)
                        }
                        
                        await websocket.send_text(json.dumps(response))
                        
                else:
                    # Неизвестная команда
                    error_response = {
                        "type": "error",
                        "message": f"Неизвестная команда: {command_type}",
                        "session_id": session_id
                    }
                    await websocket.send_text(json.dumps(error_response))
                    
            except Exception as e:
                logger.error(f"Error processing switch command: {str(e)}")
                error_response = {
                    "type": "error",
                    "message": f"Ошибка выполнения команды: {str(e)}",
                    "session_id": session_id
                }
                await websocket.send_text(json.dumps(error_response))
                
            finally:
                await db.close()

    except WebSocketDisconnect:
        chat_manager.disconnect(f"{session_id}_switch")
        logger.info(f"WebSocket switch disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket switch error: {str(e)}")
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
