"""
Сервис управления чатом
"""
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
import uuid

from models.database_models import User, LearningTrack, Chat, ChatSession
from services.chat_repository import ChatRepository
from services.openai_service import create_openai_service

logger = logging.getLogger(__name__)

class ChatManager:
    """Менеджер WebSocket соединений для чата"""
    
    def __init__(self):
        # Словарь активных соединений: session_id -> websocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Словарь активных чатов: session_id -> current_chat_id
        self.active_chats: Dict[str, str] = {}
        # Словарь истории сообщений для гостей: chat_id -> List[messages]
        self.guest_chat_history: Dict[str, List[dict]] = {}
        # Словарь соответствий сессий и чатов для гостей: session_id -> chat_id
        self.guest_session_chats: Dict[str, str] = {}
        self.history_file = "guest_history.json"
        self._load_guest_history()
        self.repo = ChatRepository()
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Подключение нового WebSocket"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")
    
    def disconnect(self, session_id: str):
        """Отключение WebSocket"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        # Убираем активный чат только из active_chats, но сохраняем в guest_session_chats
        if session_id in self.active_chats:
            del self.active_chats[session_id]
        logger.info(f"WebSocket disconnected for session: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """Отправка сообщения в конкретную сессию"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_text(json.dumps(message))

    async def create_or_get_session(self, user_id: str, track_id: str, session_name: str = None, db: AsyncSession = None) -> str:
        """Создает новую чат-сессию или возвращает существующую"""

        if not db:
            temp_session_id = str(uuid.uuid4())
            logger.info(f"Created temp session {temp_session_id}")
            return temp_session_id

        try:
            user_uuid = uuid.UUID(user_id.replace("guest_", ""))
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            return str(uuid.uuid4())

        try:
            track_uuid = uuid.UUID(track_id)
        except Exception:
            track_uuid = None

        if track_uuid:
            existing_session = await self.repo.get_active_session(user_uuid, track_uuid, db)
            if existing_session:
                logger.info(f"Found existing session {existing_session.id} for track {track_id}")
                return str(existing_session.id)

        new_session = await self.repo.create_session(
            user_uuid,
            track_uuid,
            session_name or f"Planning Session {datetime.utcnow().strftime('%d.%m %H:%M')}",
            db,
        )

        logger.info(f"Created new session {new_session.id} for track {track_id}")
        return str(new_session.id)

    async def create_or_get_chat(self, session_id: str, chat_name: str = None, chat_type: str = "planning", db: AsyncSession = None, user_id: str = None) -> str:
        """Создает новый чат или возвращает активный чат для сессии определенного типа"""
        
        if not db:
            if chat_type == "planning" and session_id in self.active_chats:
                return self.active_chats[session_id]
            temp_chat_id = str(uuid.uuid4())
            if chat_type == "planning":
                self.active_chats[session_id] = temp_chat_id
            logger.info(f"Created temporary {chat_type} chat {temp_chat_id} for session {session_id}")
            return temp_chat_id

        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError as e:
            logger.warning(f"Invalid session_id UUID format: {session_id}, error: {e}")
            temp_chat_id = str(uuid.uuid4())
            if chat_type == "planning":
                self.active_chats[session_id] = temp_chat_id
            return temp_chat_id

        try:
            existing_chat = await self.repo.get_active_chat(session_uuid, chat_type, db)
            if existing_chat:
                chat_id = str(existing_chat.id)
                if chat_type == "planning":
                    self.active_chats[session_id] = chat_id
                logger.info(f"Found existing {chat_type} chat {chat_id} for session {session_id}")
                return chat_id

            new_chat = await self.repo.create_chat(
                session_uuid,
                chat_name or f"{chat_type.title()} Chat {datetime.utcnow().strftime('%H:%M')}",
                chat_type,
                db,
            )

            chat_id = str(new_chat.id)
            if chat_type == "planning":
                self.active_chats[session_id] = chat_id

            logger.info(f"Created new {chat_type} chat {chat_id} for session {session_id}")
            return chat_id

        except Exception as e:
            logger.error(f"Failed to create chat: {e}")
            temp_chat_id = str(uuid.uuid4())
            if chat_type == "planning":
                self.active_chats[session_id] = temp_chat_id
            return temp_chat_id

    async def restore_chat_history(self, session_id: str, chat_id: str, user_id: str, db: AsyncSession = None) -> List[dict]:
        """Восстанавливает историю чата в временной последовательности"""
        
        is_guest = user_id.startswith("guest_")
        
        if is_guest or not db:
            # Для гостей возвращаем пустую историю (данные хранятся локально)
            return []
        
        try:
            session_uuid = uuid.UUID(session_id)
            chat_uuid = uuid.UUID(chat_id)
            user_uuid = uuid.UUID(user_id)
            
            # Проверяем права доступа к чату
            session = await self.repo.get_session_by_id(session_uuid, user_uuid, db)
            
            if not session:
                logger.warning(f"User {user_id} has no access to session {session_id}")
                return []
            
            messages = await self.repo.get_chat_messages(chat_uuid, db)
            
            # Формируем список сообщений для фронтенда
            chat_history = []
            for message in messages:
                chat_history.append({
                    "id": str(message.id),
                    "chat_id": str(message.chat_id),
                    "sender": message.sender_type,  # Используем только sender для фронтенда
                    "content": message.message_content,  # Используем только content для фронтенда
                    "message_type": message.message_type,
                    "timestamp": message.timestamp.strftime('%H:%M'),  # Форматируем как ожидает фронтенд
                    "ai_model_used": message.ai_model_used,
                    "tokens_used": message.tokens_used
                })
            
            logger.info(f"Restored {len(chat_history)} messages for chat {chat_id}")
            return chat_history
            
        except Exception as e:
            logger.error(f"Error restoring chat history: {e}")
            return []

    async def get_all_user_chats(self, user_id: str, session_id: str = None, db: AsyncSession = None) -> List[dict]:
        """Получает все чаты пользователя с группировкой по сессиям"""
        
        is_guest = user_id.startswith("guest_")
        
        if is_guest or not db:
            return []
        
        try:
            user_uuid = uuid.UUID(user_id)
            
            # Базовый запрос для получения чатов пользователя
            query = select(Chat, ChatSession, LearningTrack).join(
                ChatSession, Chat.session_id == ChatSession.id
            ).join(
                LearningTrack, ChatSession.track_id == LearningTrack.id
            ).where(
                ChatSession.user_id == user_uuid
            )
            
            # Фильтруем по конкретной сессии если указана
            if session_id:
                session_uuid = uuid.UUID(session_id)
                query = query.where(ChatSession.id == session_uuid)
            
            query = query.order_by(desc(ChatSession.created_at), desc(Chat.created_at))
            
            result = await db.execute(query)
            rows = result.all()
            
            # Группируем чаты по сессиям
            sessions_dict = {}
            for chat, session, track in rows:
                session_key = str(session.id)
                
                if session_key not in sessions_dict:
                    sessions_dict[session_key] = {
                        "session_id": session_key,
                        "session_name": session.session_name,
                        "track_title": track.title,
                        "track_id": str(track.id),
                        "session_created_at": session.created_at.isoformat(),
                        "chats": []
                    }
                
                sessions_dict[session_key]["chats"].append({
                    "chat_id": str(chat.id),
                    "chat_name": chat.chat_name,
                    "chat_type": chat.chat_type,
                    "status": chat.status,
                    "created_at": chat.created_at.isoformat(),
                    "updated_at": chat.updated_at.isoformat()
                })
            
            # Возвращаем список сессий с чатами
            user_chats = list(sessions_dict.values())
            logger.info(f"Retrieved {len(user_chats)} sessions with chats for user {user_id}")
            return user_chats
            
        except Exception as e:
            logger.error(f"Error getting user chats: {e}")
            return []

    async def switch_to_chat(self, session_id: str, chat_id: str, user_id: str, db: AsyncSession = None) -> dict:
        """Переключается на конкретный чат и возвращает его историю"""
        
        try:
            # Обновляем активный чат для сессии
            self.active_chats[session_id] = chat_id
            
            # Получаем историю выбранного чата
            chat_history = await self.restore_chat_history(session_id, chat_id, user_id, db)
            
            # Получаем информацию о чате
            is_guest = user_id.startswith("guest_")
            
            if not is_guest and db:
                try:
                    chat_uuid = uuid.UUID(chat_id)
                    chat = await self.repo.get_chat_by_id(chat_uuid, db)
                    
                    if chat:
                        chat_info = {
                            "chat_id": str(chat.id),
                            "chat_name": chat.chat_name,
                            "chat_type": chat.chat_type,
                            "status": chat.status,
                            "ai_context": chat.ai_context
                        }
                    else:
                        chat_info = {"chat_id": chat_id, "chat_name": "Unknown Chat"}
                        
                except Exception as e:
                    logger.error(f"Error getting chat info: {e}")
                    chat_info = {"chat_id": chat_id, "chat_name": "Chat"}
            else:
                chat_info = {"chat_id": chat_id, "chat_name": "Guest Chat"}
            
            result = {
                "success": True,
                "chat_info": chat_info,
                "history": chat_history,
                "message_count": len(chat_history)
            }
            
            logger.info(f"Switched to chat {chat_id} with {len(chat_history)} messages")
            return result
            
        except Exception as e:
            logger.error(f"Error switching to chat {chat_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "history": [],
                "message_count": 0
            }

    async def send_welcome_message(self,
                                 session_id: str,
                                 skill_area: str,
                                 user_expectations: str,
                                 difficulty_level: str,
                                 duration_hours: int,
                                 user_id: str,
                                 db: AsyncSession = None) -> Dict:
        """Отправляет приветственное сообщение с планом курса"""
        try:
            # Используем единый тип "planning" для ВСЕГО диалога
            # Включая welcome, обсуждение, финализацию - всё в одном чате
            chat_id = await self.create_or_get_chat(session_id, "Course Planning", "planning", db, user_id)
            
            # Получаем OpenAI сервис
            openai_service = await create_openai_service(user_id)
            
            if not openai_service:
                return {
                    "success": False,
                    "error": "AI сервис недоступен"
                }
            
            # Генерируем приветственное сообщение с планом
            result = await openai_service.generate_welcome_plan_message(
                skill_area=skill_area,
                user_expectations=user_expectations,
                difficulty_level=difficulty_level,
                duration_hours=duration_hours
            )
            
            if result["success"]:
                welcome_message = {
                    "type": "ai_response",
                    "message": result["content"],
                    "session_id": session_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "tokens_used": result.get("tokens_used"),
                    "model_used": openai_service.model,
                    "is_welcome": True
                }
                
                if db:
                    await self._save_ai_message_to_db(
                        chat_id,
                        result["content"],
                        openai_service.model,
                        result.get("tokens_used"),
                        db,
                    )
                    logger.info(f"Welcome message saved to DB for chat_id: {chat_id}")
                else:
                    logger.info(f"Welcome message not saved: no database session")
                
                # НЕ отправляем через WebSocket, чтобы избежать дублирования
                # Frontend получает welcome message через HTTP API и отображает в специальном стиле
                # await self.send_message(session_id, welcome_message)
                
                logger.info(f"Sent welcome message for skill: {skill_area}, chat_id: {chat_id}, tokens: {result.get('tokens_used')}")
                return {
                    "success": True,
                    "message": welcome_message,
                    "chat_id": chat_id,
                    "tokens_used": result.get("tokens_used")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Ошибка генерации приветственного сообщения")
                }
                
        except Exception as e:
            logger.error(f"Error sending welcome message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_message(self, 
                            session_id: str, 
                            message: str, 
                            user_id: str, 
                            db: AsyncSession = None,
                            message_type: str = "text",
                            chat_id: str = None):
        """Обработка сообщения от пользователя с реальным AI"""
        try:
            # Получаем или создаем chat_id
            if not chat_id:
                # Используем тот же единый тип "planning" для всего диалога
                chat_id = await self.create_or_get_chat(session_id, "Course Planning", "planning", db, user_id)
            
            # Проверяем если это гостевой пользователь
            is_guest = user_id.startswith("guest_")
            
            # Создаем временный объект пользователя для гостя
            if is_guest:
                from models.database_models import UserRole
                current_user = User(
                    id=uuid.uuid4(),
                    email=f"guest_{uuid.uuid4().hex[:8]}@guest.com",
                    password_hash="",
                    first_name="Гость",
                    last_name="Пользователь",
                    role=UserRole.STUDENT,
                    is_active=True
                )
            else:
                # Получаем пользователя из БД
                if db:
                    user_uuid = uuid.UUID(user_id)
                    result = await db.execute(select(User).where(User.id == user_uuid))
                    current_user = result.scalar_one_or_none()
                    if not current_user:
                        raise Exception("User not found")
                else:
                    raise Exception("Database session required for registered users")
            
            # Получаем OpenAI сервис
            openai_service = await create_openai_service(user_id)
            
            if not openai_service:
                # Возвращаем сообщение об ошибке
                error_response = {
                    "type": "error",
                    "message": "🚫 AI сервис временно недоступен. Проверьте настройки OpenAI API в разделе настроек.",
                    "session_id": session_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(session_id, error_response)
                return

            if db:
                await self._save_user_message_to_db(chat_id, message, message_type, db)
            else:
                logger.info("No database session provided, user message not saved")

            # Получаем контекст трека и историю чата для AI
            track_context = await self._get_track_context(session_id, db) if db else ""
            chat_history = await self._get_chat_history(chat_id, db) if db else []

            # Логируем что получил AI для отладки
            logger.info(f"Sending to AI: {len(chat_history)} history messages + 1 new message for chat {chat_id}")
            if chat_history:
                first_msg = chat_history[0]
                logger.debug(f"First message in history: {first_msg['role']} - {first_msg['content'][:100]}...")

            # Формируем сообщения для AI в правильном формате
            messages = chat_history + [{"role": "user", "content": message}]
            
            logger.debug(f"Total messages to AI: {len(messages)} (including {len(chat_history)} from history)")

            # Генерируем ответ от AI
            ai_result = await openai_service.generate_chat_response(
                messages=messages,
                context=track_context
            )

            if ai_result["success"]:
                ai_response = ai_result["content"]
                tokens_used = ai_result.get("tokens_used", 0)

                if db:
                    await self._save_ai_message_to_db(chat_id, ai_response, openai_service.model, tokens_used, db)
                else:
                    logger.info("No database session provided, AI response not saved")

                # Формируем ответ для WebSocket
                response_message = {
                    "type": "ai_response",
                    "message": ai_response,
                    "session_id": session_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "tokens_used": tokens_used,
                    "model_used": openai_service.model
                }

                # Отправляем ответ через WebSocket
                await self.send_message(session_id, response_message)
                
                logger.info(f"Processed message in chat {chat_id}, tokens used: {tokens_used}")

            else:
                # Отправляем сообщение об ошибке AI
                error_response = {
                    "type": "error",
                    "message": f"🚫 Ошибка AI: {ai_result.get('error', 'Неизвестная ошибка')}",
                    "session_id": session_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(session_id, error_response)
                logger.error(f"AI error: {ai_result.get('error')}")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            
            # Отправляем общее сообщение об ошибке
            error_response = {
                "type": "error",
                "message": f"🚫 Ошибка обработки сообщения: {str(e)}",
                "session_id": session_id,
                "chat_id": chat_id or "unknown",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.send_message(session_id, error_response)

    async def _get_track_context(self, session_id: str, db: AsyncSession) -> str:
        """Получает контекст трека для AI"""
        try:
            session_uuid = uuid.UUID(session_id)
            
            # Получаем информацию о треке через сессию
            result = await db.execute(
                select(LearningTrack, ChatSession).join(
                    ChatSession, LearningTrack.id == ChatSession.track_id
                ).where(ChatSession.id == session_uuid)
            )
            row = result.first()
            
            if row:
                track, session = row
                context = f"""
Контекст трека обучения:
- Название: {track.title}
- Область навыков: {track.skill_area}
- Уровень сложности: {track.difficulty_level.value if track.difficulty_level else 'не указан'}
- Планируемая длительность: {track.estimated_duration_hours} часов
- Ожидания: {track.user_expectations}
- Статус: {track.status.value if track.status else 'планирование'}
"""
                if track.ai_generated_plan:
                    context += f"\nТекущий план: {json.dumps(track.ai_generated_plan, ensure_ascii=False)}"
                return context
            else:
                return "Контекст трека не найден"
                
        except Exception as e:
            logger.error(f"Error getting track context: {e}")
            return "Ошибка получения контекста"

    async def _get_chat_history(self, chat_id: str, db: AsyncSession, limit: int = 50) -> List[dict]:
        """Получает историю чата для AI (все сообщения в хронологическом порядке)"""
        try:
            if not db:
                logger.info(f"No database session provided for chat {chat_id}, returning empty history")
                return []
            
            # Проверяем что chat_id является валидным UUID
            try:
                chat_uuid = uuid.UUID(chat_id)
            except ValueError:
                logger.warning(f"Invalid chat_id UUID format: {chat_id}")
                return []
            
            messages = await self.repo.get_chat_messages(chat_uuid, db, limit)
            
            # Формируем историю для AI в правильном формате
            history = []
            for message in messages:
                history.append({
                    "sender_type": message.sender_type,  # Используем sender_type для консистентности с БД
                    "content": message.message_content,
                    "timestamp": message.timestamp.isoformat()
                })
            
            logger.info(f"Retrieved {len(history)} messages from chat {chat_id} for AI context")
            
            # Логируем первые несколько сообщений для отладки
            if history:
                logger.debug(f"First message in chat {chat_id}: {history[0]['role']} - {history[0]['content'][:100]}...")
                if len(history) > 1:
                    logger.debug(f"Last message in chat {chat_id}: {history[-1]['role']} - {history[-1]['content'][:100]}...")
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting chat history for chat {chat_id}: {e}")
            return []

    async def _save_user_message_to_db(self, chat_id: str, message: str, message_type: str, db: AsyncSession):
        """Сохраняет сообщение пользователя в БД"""
        try:
            if not db:
                logger.info(f"No database session provided, message not saved")
                return
                
            try:
                chat_uuid = uuid.UUID(chat_id)
            except ValueError:
                logger.info(f"Invalid chat_id UUID format: {chat_id}, message saved only to guest history")
                return
            
            await self.repo.save_user_message(chat_uuid, message, message_type, db)
            logger.info(f"Saved user message to chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error saving user message: {e}")

    async def _save_ai_message_to_db(self, chat_id: str, message: str, model: str, tokens_used: int, db: AsyncSession):
        """Сохраняет сообщение AI в БД"""
        try:
            if not db:
                logger.info(f"No database session provided, AI message not saved")
                return
                
            try:
                chat_uuid = uuid.UUID(chat_id)
            except ValueError:
                logger.info(f"Invalid chat_id UUID format: {chat_id}")
                return
            
            await self.repo.save_ai_message(chat_uuid, message, model, tokens_used, db)
            logger.info(f"Saved AI message to chat {chat_id}: model={model}, tokens={tokens_used}, content_length={len(message)}")
            
        except Exception as e:
            logger.error(f"Error saving AI message to chat {chat_id}: {e}")
            await db.rollback()  # Откатываем транзакцию в случае ошибки

    def _save_message_to_guest_history(self, chat_id: str, role: str, content: str):
        """Сохраняет сообщение в память для гостевых чатов"""
        if chat_id not in self.guest_chat_history:
            self.guest_chat_history[chat_id] = []
        
        # Конвертируем role в sender_type для консистентности с БД форматом
        sender_type = role
        if role == "assistant":
            sender_type = "ai"
        elif role == "user":
            sender_type = "user"
        
        self.guest_chat_history[chat_id].append({
            "sender_type": sender_type,  # Используем sender_type как в БД
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Ограничиваем историю 100 сообщениями для экономии памяти
        if len(self.guest_chat_history[chat_id]) > 100:
            self.guest_chat_history[chat_id] = self.guest_chat_history[chat_id][-100:]
        
        logger.debug(f"Saved {sender_type} message to guest history for chat {chat_id}")
        self._save_guest_history()
    
    def _get_guest_chat_history(self, chat_id: str) -> List[dict]:
        """Получает историю гостевого чата из памяти"""
        return self.guest_chat_history.get(chat_id, [])

    def _load_guest_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.guest_chat_history = json.load(f)
            except Exception:
                self.guest_chat_history = {}

    def _save_guest_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.guest_chat_history, f)
        except Exception:
            pass

    async def broadcast_to_session(self, session_id: str, message: dict):
        """Отправляет сообщение всем подключениям в сессии"""
        await self.send_message(session_id, message)

    def get_active_connections_count(self) -> int:
        """Возвращает количество активных соединений"""
        return len(self.active_connections)

    def is_session_active(self, session_id: str) -> bool:
        """Проверяет активность сессии"""
        return session_id in self.active_connections

    def get_current_chat_id(self, session_id: str) -> str:
        """Получает текущий chat_id для сессии"""
        return self.active_chats.get(session_id)

    async def finalize_course_plan(self,
                                 session_id: str,
                                 skill_area: str,
                                 track_id: str,
                                 user_id: str,
                                 db: AsyncSession = None) -> Dict:
        """Финализирует план курса из истории чата и создает модули"""
        try:
            # Используем тот же единый чат планирования
            chat_id = await self.create_or_get_chat(
                session_id, 
                "Course Planning", 
                "planning", 
                db, 
                user_id
            )
            
            # Получаем историю чата для извлечения плана
            is_guest = user_id.startswith("guest_")

            if db:
                chat_history = await self._get_chat_history(chat_id, db, limit=50)
            else:
                # Если нет доступа к БД (редкий случай), читаем из гостевой истории
                chat_history = self._get_guest_chat_history(chat_id)

            # Ищем последнее AI сообщение с планом
            course_plan = ""
            for msg in reversed(chat_history):
                if msg.get("sender_type") == "ai" or msg.get("role") == "assistant":
                    course_plan = msg["content"]
                    break
            
            if not course_plan.strip():
                error_message = {
                    "type": "error",
                    "message": "🚫 Не найден план для финализации. Сначала обсудите план курса с AI.",
                    "session_id": session_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(session_id, error_message)
                return {"success": False, "error": "План курса не найден в истории чата"}
            
            # Получаем OpenAI сервис
            openai_service = await create_openai_service(user_id)
            
            if not openai_service:
                error_message = {
                    "type": "error",
                    "message": "🚫 AI сервис недоступен для финализации плана",
                    "session_id": session_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(session_id, error_message)
                return {"success": False, "error": "AI сервис недоступен"}
            
            # Генерируем финальные модули через AI на основе плана из чата
            result = await openai_service.generate_finalized_modules(course_plan, skill_area)
            
            if result["success"]:
                try:
                    # Парсим JSON модулей
                    modules_data = json.loads(result["content"])
                    
                    # Сохраняем модули в БД (только для зарегистрированных пользователей)
                    modules_count = 0
                    
                    if not is_guest and db:
                        from models.database_models import CourseModule
                        from sqlalchemy import delete
                        
                        track_uuid = uuid.UUID(track_id)
                        
                        # Удаляем старые модули трека
                        await db.execute(
                            delete(CourseModule).where(CourseModule.track_id == track_uuid)
                        )
                        
                        # Создаем новые модули
                        for i, module_data in enumerate(modules_data, 1):
                            new_module = CourseModule(
                                track_id=track_uuid,
                                module_number=i,
                                title=module_data.get("title", f"Модуль {i}"),
                                description=module_data.get("description", ""),
                                learning_objectives=module_data.get("learning_objectives", []),
                                estimated_duration_hours=module_data.get("estimated_duration_hours", 1),
                                ai_generated_content=module_data,
                                status="not_started"
                            )
                            db.add(new_module)
                            modules_count += 1
                        
                        # Обновляем статус трека
                        track_result = await db.execute(
                            select(LearningTrack).where(LearningTrack.id == track_uuid)
                        )
                        track = track_result.scalar_one_or_none()
                        if track:
                            from models.database_models import TrackStatus
                            track.status = TrackStatus.ACTIVE
                        
                        await db.commit()
                        logger.info(f"Created {modules_count} modules for track {track_id}")
                    
                    # Сохраняем сообщение о финализации в тот же чат планирования
                    finalization_message = f"🎉 **План курса финализирован!**\n\nСоздано модулей: {len(modules_data)}\n\nМодули:\n"
                    for i, module in enumerate(modules_data, 1):
                        finalization_message += f"**{i}. {module.get('title', 'Модуль')}** ({module.get('estimated_duration_hours', 1)} ч.)\n"
                    
                    finalization_message += "\n📚 Модули курса созданы и готовы к изучению!"
                    
                    if db:
                        await self._save_ai_message_to_db(
                            chat_id,
                            finalization_message,
                            openai_service.model,
                            result.get("tokens_used", 0),
                            db,
                        )
                    else:
                        logger.info("No database session provided, finalization message not saved")
                    
                    # Отправляем результат через WebSocket
                    response_message = {
                        "type": "finalization_complete",
                        "message": finalization_message,
                        "session_id": session_id,
                        "chat_id": chat_id,
                        "modules_created": len(modules_data),
                        "track_id": track_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.send_message(session_id, response_message)
                    
                    return {
                        "success": True,
                        "modules_count": len(modules_data),
                        "modules": modules_data,
                        "chat_id": chat_id
                    }
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse modules JSON: {e}")
                    
                    # Отправляем сообщение об ошибке
                    error_message = {
                        "type": "error",
                        "message": "🚫 Ошибка парсинга данных модулей. Попробуйте еще раз.",
                        "session_id": session_id,
                        "chat_id": chat_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.send_message(session_id, error_message)
                    return {"success": False, "error": "Ошибка парсинга данных"}
            else:
                # AI ошибка
                error_message = {
                    "type": "error",
                    "message": f"🚫 Ошибка AI при финализации: {result.get('error', 'Неизвестная ошибка')}",
                    "session_id": session_id,
                    "chat_id": chat_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_message(session_id, error_message)
                return {"success": False, "error": result.get("error", "AI ошибка")}
                
        except Exception as e:
            logger.error(f"Error finalizing course plan: {str(e)}")
            return {"success": False, "error": str(e)}

    async def process_planning_chat_message(self,
                                            session_id: str,
                                            user_message: str,
                                            user_id: str,
                                            track_context: str = "",
                                            chat_id: str = None,
                                            db: AsyncSession = None) -> Dict:
        """Обрабатывает сообщение пользователя в чате планирования через HTTP"""

        try:
            chat_id = chat_id or await self.create_or_get_chat(
                session_id,
                "Course Planning",
                "planning",
                db,
                user_id,
            )

            is_guest = user_id.startswith("guest_")

            if db:
                await self._save_user_message_to_db(chat_id, user_message, "text", db)
            else:
                logger.info("No database session provided, user message not saved")

            if not track_context:
                track_context = await self._get_track_context(session_id, db) if db else ""

            chat_history = await self._get_chat_history(chat_id, db) if (db or is_guest) else []

            messages = chat_history + [{"role": "user", "content": user_message}]

            openai_service = await create_openai_service(user_id)
            if not openai_service:
                return {"success": False, "error": "AI сервис недоступен", "chat_id": chat_id}

            ai_result = await openai_service.generate_chat_response(
                messages=messages,
                context=track_context,
            )

            if ai_result["success"]:
                ai_response = ai_result["content"]
                tokens_used = ai_result.get("tokens_used", 0)

                if db:
                    await self._save_ai_message_to_db(
                        chat_id,
                        ai_response,
                        openai_service.model,
                        tokens_used,
                        db,
                    )
                else:
                    logger.info("No database session provided, AI response not saved")

                return {
                    "success": True,
                    "response": ai_response,
                    "chat_id": chat_id,
                    "tokens_used": tokens_used,
                }
            else:
                return {
                    "success": False,
                    "error": ai_result.get("error", "AI ошибка"),
                    "chat_id": chat_id,
                }

        except Exception as e:
            logger.error(f"Error processing planning chat message: {str(e)}")
            return {"success": False, "error": str(e), "chat_id": chat_id}

    async def restore_existing_chat_if_any(self, session_id: str, user_id: str, db: AsyncSession = None) -> Dict:
        """Восстанавливает существующий диалог если пользователь возвращается на страницу"""
        try:
            is_guest = user_id.startswith("guest_")
            
            # Для гостей проверяем память
            if is_guest or not db:
                # Сначала проверяем есть ли активный чат для этой сессии
                active_chat_id = self.active_chats.get(session_id)
                
                # Если нет активного, проверяем постоянное хранилище для гостей
                if not active_chat_id:
                    active_chat_id = self.guest_session_chats.get(session_id)
                    # Восстанавливаем в активные если найден
                    if active_chat_id:
                        self.active_chats[session_id] = active_chat_id
                
                if active_chat_id and active_chat_id in self.guest_chat_history:
                    chat_history = self._get_guest_chat_history(active_chat_id)
                    
                    # Конвертируем формат для фронтенда
                    frontend_history = []
                    for msg in chat_history:
                        frontend_history.append({
                            "id": f"guest-{len(frontend_history)}",
                            "chat_id": active_chat_id,
                            "sender": msg.get("sender_type", msg.get("role", "user")),  # Поддерживаем оба формата
                            "content": msg["content"],
                            "message_type": "text",
                            "timestamp": msg["timestamp"],
                            "ai_model_used": None,
                            "tokens_used": None
                        })
                    
                    logger.info(f"Restored guest chat {active_chat_id} with {len(frontend_history)} messages for session {session_id}")
                    
                    return {
                        "success": True,
                        "has_existing_chat": True,
                        "chat_id": active_chat_id,
                        "chat_info": {
                            "chat_id": active_chat_id,
                            "chat_name": "Guest Planning Chat",
                            "chat_type": "planning",
                            "created_at": datetime.utcnow().isoformat()
                        },
                        "history": frontend_history,
                        "message_count": len(frontend_history)
                    }
                
                # Нет сохраненной истории для гостей
                return {
                    "success": True,
                    "has_existing_chat": False,
                    "chat_id": None,
                    "history": []
                }
            
            # Для зарегистрированных пользователей ищем в БД
            try:
                session_uuid = uuid.UUID(session_id)
            except ValueError:
                logger.warning(f"Invalid session_id UUID format: {session_id}")
                return {
                    "success": True,
                    "has_existing_chat": False,
                    "chat_id": None,
                    "history": []
                }
            
            existing_chat = await self.repo.get_active_chat(session_uuid, "planning", db)
            
            if existing_chat:
                chat_id = str(existing_chat.id)
                
                # Получаем историю существующего чата
                chat_history = await self.restore_chat_history(session_id, chat_id, user_id, db)
                
                # Обновляем активный чат в памяти
                self.active_chats[session_id] = chat_id
                
                logger.info(f"Restored existing chat {chat_id} with {len(chat_history)} messages for session {session_id}")
                
                return {
                    "success": True,
                    "has_existing_chat": True,
                    "chat_id": chat_id,
                    "chat_info": {
                        "chat_id": chat_id,
                        "chat_name": existing_chat.chat_name,
                        "chat_type": existing_chat.chat_type,
                        "created_at": existing_chat.created_at.isoformat()
                    },
                    "history": chat_history,
                    "message_count": len(chat_history)
                }
            else:
                # Нет существующего чата
                return {
                    "success": True,
                    "has_existing_chat": False,
                    "chat_id": None,
                    "history": []
                }
                
        except Exception as e:
            logger.error(f"Error restoring existing chat: {e}")
            return {
                "success": False,
                "error": str(e),
                "has_existing_chat": False,
                "chat_id": None,
                "history": []
            }

    async def create_module_learning_chat(self,
                                        session_id: str,
                                        track_id: str,
                                        module_id: str,
                                        user_id: str,
                                        module_summary: str,
                                        db: AsyncSession = None) -> Dict:
        """Создает новый чат для изучения модуля и сохраняет конспект"""
        
        try:
            is_guest = user_id.startswith("guest_")
            
            # Создаем название чата для модуля
            chat_name = f"Модуль: {module_id}"
            chat_type = "module_learning"
            
            # Создаем чат
            if not is_guest and db:
                try:
                    session_uuid = uuid.UUID(session_id)
                    user_uuid = uuid.UUID(user_id)
                    
                    # Проверяем track_id и module_id - могут быть не UUID
                    try:
                        track_uuid = uuid.UUID(track_id)
                    except ValueError:
                        logger.warning(f"Non-UUID track_id: {track_id}, creating guest chat")
                        is_guest = True
                        
                    try:
                        module_uuid = uuid.UUID(module_id)
                    except ValueError:
                        # module_id может быть числовым
                        module_uuid = None
                        logger.info(f"Non-UUID module_id: {module_id}")
                        
                except ValueError:
                    logger.error(f"Invalid UUID format in module chat creation")
                    is_guest = True
                
                if not is_guest:
                    # Создаем чат в БД
                    new_chat = Chat(
                        id=uuid.uuid4(),
                        session_id=session_uuid,
                        chat_name=chat_name,
                        chat_type=chat_type,
                        created_by=user_uuid,
                        status="active",
                        track_id=track_uuid if 'track_uuid' in locals() else None,
                        module_id=module_uuid if module_uuid else None
                    )
                    
                    db.add(new_chat)
                    await db.flush()
                    
                    chat_id = str(new_chat.id)
                    
                    # Сохраняем конспект как первое сообщение от AI
                    await self._save_ai_message_to_db(
                        chat_id=chat_id,
                        message=module_summary,
                        model="system",
                        tokens_used=0,
                        db=db
                    )
                    
                    await db.commit()
                    
            if is_guest or not db:
                # Для гостей создаем временный чат
                chat_id = f"module_chat_{generate_id()}"
                
                # Инициализируем историю чата в памяти
                self.guest_chat_history[chat_id] = [
                    {
                        "role": "assistant",
                        "content": module_summary,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
                
                # Связываем чат с сессией
                self.guest_session_chats[session_id] = chat_id
            
            # Обновляем активный чат
            self.active_chats[session_id] = chat_id
            
            logger.info(f"Created module learning chat {chat_id} for module {module_id}")
            
            return {
                "success": True,
                "chat_id": chat_id,
                "chat_type": chat_type
            }
            
        except Exception as e:
            logger.error(f"Error creating module learning chat: {str(e)}")
            return {"success": False, "error": str(e)}

    async def process_module_chat_message(self,
                                        session_id: str,
                                        chat_id: str,
                                        user_message: str,
                                        user_id: str,
                                        track_context: str = "",
                                        db: AsyncSession = None) -> Dict:
        """Обрабатывает сообщение пользователя в чате модуля"""
        
        try:
            is_guest = user_id.startswith("guest_")
            
            # Сохраняем сообщение пользователя
            if not is_guest and db:
                await self._save_user_message_to_db(chat_id, user_message, "text", db)
            else:
                self._save_message_to_guest_history(chat_id, "user", user_message)
            
            # Получаем историю чата для контекста
            if not is_guest and db:
                try:
                    chat_history = await self._get_chat_history(chat_id, db, limit=10)
                    
                    # Конвертируем для OpenAI
                    messages = []
                    for msg in chat_history:
                        role = "user" if msg["sender_type"] == "user" else "assistant"
                        messages.append({"role": role, "content": msg["content"]})
                        
                    logger.info(f"Retrieved {len(messages)} messages from DB for AI context")
                    
                except Exception as e:
                    # Если ошибка с БД, переключаемся на гостевую историю
                    logger.warning(f"Failed to get DB chat history, using guest history: {e}")
                    guest_history = self._get_guest_chat_history(chat_id)
                    messages = []
                    for msg in guest_history:
                        # Безопасно обрабатываем сообщения любого формата
                        if "sender_type" in msg:
                            # Новый формат с sender_type
                            role = "user" if msg["sender_type"] == "user" else "assistant"
                            messages.append({"role": role, "content": msg["content"]})
                        elif "role" in msg:
                            # Старый формат с role (для совместимости)
                            messages.append({"role": msg["role"], "content": msg["content"]})
                        else:
                            logger.warning(f"Unknown message format: {msg}")
                    
                    logger.info(f"Retrieved {len(messages)} messages from guest chat {chat_id} for AI context")
            else:
                guest_history = self._get_guest_chat_history(chat_id)
                messages = []
                for msg in guest_history:
                    # Безопасно обрабатываем сообщения любого формата
                    if "sender_type" in msg:
                        # Новый формат с sender_type
                        role = "user" if msg["sender_type"] == "user" else "assistant"
                        messages.append({"role": role, "content": msg["content"]})
                    elif "role" in msg:
                        # Старый формат с role (для совместимости)
                        messages.append({"role": msg["role"], "content": msg["content"]})
                    else:
                        logger.warning(f"Unknown message format in guest history: {msg}")
                
                logger.info(f"Retrieved {len(messages)} messages from guest chat {chat_id} for AI context")
            
            # Добавляем текущее сообщение пользователя
            messages.append({"role": "user", "content": user_message})
            
            # Создаем системное сообщение с контекстом модуля
            system_message = f"""Ты - ИИ-помощник для изучения конкретного модуля курса. 

Контекст:
{track_context}

Ты помогаешь студенту изучить материал модуля. В начале чата ты предоставил конспект модуля.

Твоя роль:
- Отвечать на вопросы по материалу модуля
- Объяснять сложные концепции простыми словами
- Давать дополнительные примеры
- Предлагать практические упражнения
- Проверять понимание материала
- Мотивировать к изучению

Стиль общения:
- Дружелюбный и поддерживающий
- Структурированные ответы с примерами
- Используй эмодзи для улучшения восприятия
- Адаптируй сложность объяснений под уровень вопросов

Помни: ты фокусируешься именно на материале этого модуля, но можешь упоминать связи с другими темами курса."""
            
            # Вставляем системное сообщение в начало
            messages.insert(0, {"role": "system", "content": system_message})
            
            # Получаем OpenAI сервис
            openai_service = await create_openai_service(user_id)
            
            # Генерируем ответ
            result = await openai_service.generate_chat_response(messages)
            
            if result["success"]:
                ai_response = result["content"]
                tokens_used = result.get("tokens_used", 0)
                
                # Сохраняем ответ AI
                if not is_guest and db:
                    await self._save_ai_message_to_db(
                        chat_id, 
                        ai_response, 
                        openai_service.model, 
                        tokens_used, 
                        db
                    )
                else:
                    self._save_message_to_guest_history(chat_id, "assistant", ai_response)
                
                return {
                    "success": True,
                    "response": ai_response,
                    "chat_id": chat_id,
                    "tokens_used": tokens_used
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "AI ошибка"),
                    "chat_id": chat_id
                }
                
        except Exception as e:
            logger.error(f"Error processing module chat message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "chat_id": chat_id
            }

    async def complete_module(self,
                            session_id: str,
                            track_id: str,
                            module_id: str,
                            user_id: str,
                            db: AsyncSession = None) -> Dict:
        """Завершает изучение модуля и обновляет прогресс"""
        
        try:
            is_guest = user_id.startswith("guest_")
            
            if not is_guest and db:
                try:
                    # Пытаемся парсить как UUID только для зарегистрированных пользователей
                    track_uuid = uuid.UUID(track_id)
                    module_uuid = uuid.UUID(module_id)
                    user_uuid = uuid.UUID(user_id)
                    
                    # Обновляем статус модуля в БД
                    from models.database_models import CourseModule, ModuleStatus
                    
                    result = await db.execute(
                        select(CourseModule).where(
                            and_(
                                CourseModule.id == module_uuid,
                                CourseModule.track_id == track_uuid
                            )
                        )
                    )
                    module = result.scalar_one_or_none()
                    
                    if module:
                        module.status = ModuleStatus.COMPLETED
                        module.progress_percentage = 100
                        module.completed_at = datetime.utcnow()
                        
                        await db.commit()
                        
                        logger.info(f"Module {module_id} completed by user {user_id}")
                        
                        return {
                            "success": True,
                            "message": "Модуль успешно завершен!",
                            "module_id": module_id,
                            "status": "completed"
                        }
                    else:
                        return {"success": False, "error": "Module not found"}
                        
                except (ValueError, TypeError) as e:
                    # ID не в формате UUID - работаем как с гостем
                    logger.info(f"Non-UUID module/track ID for completion: track_id={track_id}, module_id={module_id}")
                    # Падаем в гостевой режим
                    pass
            
            # Для гостей или при ошибке парсинга UUID возвращаем успех
            return {
                "success": True,
                "message": "Модуль завершен (локальный режим)",
                "module_id": module_id,
                "status": "completed"
            }
                
        except Exception as e:
            logger.error(f"Error completing module: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_module_chat_history(self,
                                    session_id: str,
                                    track_id: str,
                                    module_id: str,
                                    user_id: str,
                                    db: AsyncSession = None) -> Dict:
        """Получает историю чата модуля"""
        
        try:
            is_guest = user_id.startswith("guest_")
            
            # Для гостей ищем в памяти
            if is_guest or not db:
                # Генерируем возможные ключи чата для поиска
                chat_patterns = [
                    f"module_chat_{track_id}_{module_id}",
                    f"module_chat_{generate_id()}",  # Временный
                ]
                
                # Ищем в активных чатах сессии
                active_chat_id = self.active_chats.get(session_id)
                if active_chat_id and active_chat_id in self.guest_chat_history:
                    history = self._get_guest_chat_history(active_chat_id)
                    
                    # Конвертируем формат для фронтенда
                    frontend_history = []
                    for msg in history:
                        # Форматируем timestamp в формат HH:MM
                        try:
                            if msg["timestamp"]:
                                # Если timestamp в ISO формате, парсим его
                                if isinstance(msg["timestamp"], str) and "T" in msg["timestamp"]:
                                    from datetime import datetime
                                    dt = datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00'))
                                    formatted_time = dt.strftime('%H:%M')
                                else:
                                    formatted_time = msg["timestamp"]
                            else:
                                from datetime import datetime
                                formatted_time = datetime.now().strftime('%H:%M')
                        except:
                            from datetime import datetime
                            formatted_time = datetime.now().strftime('%H:%M')
                            
                        frontend_history.append({
                            "id": f"guest-{len(frontend_history)}",
                            "chat_id": active_chat_id,
                            "sender": msg.get("sender_type", msg.get("role", "user")),  # Поддерживаем оба формата
                            "content": msg["content"],
                            "message_type": "text",
                            "timestamp": formatted_time,
                            "ai_model_used": None,
                            "tokens_used": None
                        })
                    
                    return {
                        "success": True,
                        "history": frontend_history,
                        "chat_id": active_chat_id
                    }
                
                return {
                    "success": True,
                    "history": [],
                    "chat_id": None
                }
            
            # Для зарегистрированных пользователей ищем в БД
            try:
                session_uuid = uuid.UUID(session_id)
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                return {"success": False, "error": "Invalid UUID format"}
            
            module_chat = await self.repo.get_active_chat(session_uuid, "module_learning", db)
            
            if module_chat:
                chat_id = str(module_chat.id)
                
                # Получаем историю сообщений
                history = await self.restore_chat_history(session_id, chat_id, user_id, db)
                
                return {
                    "success": True,
                    "history": history,
                    "chat_id": chat_id
                }
            else:
                return {
                    "success": True,
                    "history": [],
                    "chat_id": None
                }
                
        except Exception as e:
            logger.error(f"Error getting module chat history: {str(e)}")
            return {"success": False, "error": str(e)}

def generate_id() -> str:
    """Генерирует уникальный ID"""
    return str(uuid.uuid4())

# Создаем глобальный экземпляр менеджера чата
chat_manager = ChatManager() 