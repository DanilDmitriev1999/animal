"""
Роутер чата планирования
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from models.database import get_db
from models.database_models import User, LearningTrack, ChatSession, Chat, ChatMessage
from routers.auth import get_current_user
from services.chat_service import chat_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic модели
class ChatSessionCreate(BaseModel):
    track_id: str
    session_name: str

class ChatSessionResponse(BaseModel):
    id: str
    track_id: str
    session_name: str
    status: str
    created_at: datetime
    updated_at: datetime

class ChatCreate(BaseModel):
    session_id: str
    chat_name: Optional[str] = None
    chat_type: str = "planning"

class ChatResponse(BaseModel):
    id: str
    session_id: str
    chat_name: str
    chat_type: str
    status: str
    created_at: datetime
    updated_at: datetime

class ChatMessageResponse(BaseModel):
    id: str
    chat_id: str
    sender_type: str
    message_content: str
    message_type: str
    ai_model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    timestamp: datetime

class ChatHistoryResponse(BaseModel):
    success: bool
    chat_info: dict
    history: List[dict]
    message_count: int

class UserChatsResponse(BaseModel):
    session_id: str
    session_name: str
    track_title: str
    track_id: str
    session_created_at: str
    chats: List[dict]

class SwitchChatRequest(BaseModel):
    chat_id: str

class RestoreExistingChatResponse(BaseModel):
    success: bool
    has_existing_chat: bool
    chat_id: Optional[str] = None
    chat_info: Optional[dict] = None
    history: List[dict] = []
    message_count: int = 0

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание чат-сессии для планирования курса"""
    
    # Для гостевого пользователя создаем сессию в памяти
    if current_user.email.startswith("guest_"):
        guest_session = ChatSessionResponse(
            id=str(uuid.uuid4()),
            track_id=session_data.track_id,
            session_name=session_data.session_name,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        logger.info(f"Created guest chat session: {guest_session.id}")
        return guest_session
    
    try:
        # Проверяем что трек существует и принадлежит пользователю
        track_uuid = uuid.UUID(session_data.track_id)
        result = await db.execute(
            select(LearningTrack).where(
                LearningTrack.id == track_uuid,
                LearningTrack.user_id == current_user.id
            )
        )
        track = result.scalar_one_or_none()
        
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )
        
        # Создаем новую чат-сессию
        new_session = ChatSession(
            track_id=track.id,
            user_id=current_user.id,
            session_name=session_data.session_name,
            status="active"
        )
        
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        
        # Формируем ответ
        session_response = ChatSessionResponse(
            id=str(new_session.id),
            track_id=str(new_session.track_id),
            session_name=new_session.session_name,
            status=new_session.status,
            created_at=new_session.created_at,
            updated_at=new_session.updated_at
        )
        
        logger.info(f"Created chat session: {new_session.id} for track: {track.title}")
        return session_response
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )

@router.post("/chats", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового чата в рамках сессии"""
    
    # Для гостевого пользователя создаем чат в памяти
    if current_user.email.startswith("guest_"):
        guest_chat = ChatResponse(
            id=str(uuid.uuid4()),
            session_id=chat_data.session_id,
            chat_name=chat_data.chat_name or f"Chat {datetime.utcnow().strftime('%H:%M')}",
            chat_type=chat_data.chat_type,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        logger.info(f"Created guest chat: {guest_chat.id}")
        return guest_chat
    
    try:
        session_uuid = uuid.UUID(chat_data.session_id)
        
        # Проверяем что сессия существует и принадлежит пользователю
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_uuid,
                ChatSession.user_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Создаем новый чат
        new_chat = Chat(
            session_id=session.id,
            chat_name=chat_data.chat_name or f"Chat {datetime.utcnow().strftime('%H:%M')}",
            chat_type=chat_data.chat_type,
            status="active"
        )
        
        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)
        
        # Формируем ответ
        chat_response = ChatResponse(
            id=str(new_chat.id),
            session_id=str(new_chat.session_id),
            chat_name=new_chat.chat_name,
            chat_type=new_chat.chat_type,
            status=new_chat.status,
            created_at=new_chat.created_at,
            updated_at=new_chat.updated_at
        )
        
        logger.info(f"Created chat: {new_chat.id} in session: {session.id}")
        return chat_response
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat"
        )

@router.get("/sessions/{session_id}/chats", response_model=List[ChatResponse])
async def get_session_chats(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех чатов в сессии"""
    
    # Для гостевых пользователей возвращаем пустой список
    if current_user.email.startswith("guest_"):
        return []
    
    try:
        # Пытаемся распарсить как UUID, если не получается - считаем это временным ID
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            logger.warning(f"Non-UUID session_id received: {session_id}, treating as temporary session")
            return []  # Для временных сессий возвращаем пустой список
        
        # Проверяем доступ к сессии
        session_result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_uuid,
                ChatSession.user_id == current_user.id
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Получаем все чаты сессии
        chats_result = await db.execute(
            select(Chat).where(
                Chat.session_id == session_uuid
            ).order_by(desc(Chat.created_at))
        )
        chats = chats_result.scalars().all()
        
        # Формируем ответ
        chat_responses = []
        for chat in chats:
            chat_responses.append(ChatResponse(
                id=str(chat.id),
                session_id=str(chat.session_id),
                chat_name=chat.chat_name,
                chat_type=chat.chat_type,
                status=chat.status,
                created_at=chat.created_at,
                updated_at=chat.updated_at
            ))
        
        logger.info(f"Retrieved {len(chat_responses)} chats for session {session_id}")
        return chat_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session chats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session chats"
        )

@router.get("/chats/{chat_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение сообщений чата"""
    
    # Для гостевых пользователей возвращаем пустой список
    if current_user.email.startswith("guest_"):
        return []
    
    try:
        chat_uuid = uuid.UUID(chat_id)
        
        # Проверяем доступ к чату через сессию
        result = await db.execute(
            select(Chat, ChatSession).join(
                ChatSession, Chat.session_id == ChatSession.id
            ).where(
                and_(
                    Chat.id == chat_uuid,
                    ChatSession.user_id == current_user.id
                )
            )
        )
        row = result.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found or access denied"
            )
        
        # Получаем сообщения чата в хронологическом порядке
        messages_result = await db.execute(
            select(ChatMessage).where(
                ChatMessage.chat_id == chat_uuid
            ).order_by(ChatMessage.timestamp.asc())
        )
        messages = messages_result.scalars().all()
        
        # Формируем ответ
        message_responses = []
        for message in messages:
            message_responses.append(ChatMessageResponse(
                id=str(message.id),
                chat_id=str(message.chat_id),
                sender_type=message.sender_type,
                message_content=message.message_content,
                message_type=message.message_type,
                ai_model_used=message.ai_model_used,
                tokens_used=message.tokens_used,
                timestamp=message.timestamp
            ))
        
        logger.info(f"Retrieved {len(message_responses)} messages for chat {chat_id}")
        return message_responses
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat messages"
        )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_user_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех чат-сессий пользователя"""
    
    # Для гостевых пользователей возвращаем пустой список
    if current_user.email.startswith("guest_"):
        return []
    
    try:
        # Получаем все сессии пользователя
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.user_id == current_user.id
            ).order_by(desc(ChatSession.created_at))
        )
        sessions = result.scalars().all()
        
        # Формируем ответ
        session_responses = []
        for session in sessions:
            session_responses.append(ChatSessionResponse(
                id=str(session.id),
                track_id=str(session.track_id) if session.track_id else "",
                session_name=session.session_name,
                status=session.status,
                created_at=session.created_at,
                updated_at=session.updated_at
            ))
        
        logger.info(f"Retrieved {len(session_responses)} sessions for user {current_user.id}")
        return session_responses
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user sessions"
        )

@router.put("/sessions/{session_id}/status")
async def update_session_status(
    session_id: str,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление статуса сессии"""
    
    # Гостевые пользователи не могут обновлять статус
    if current_user.email.startswith("guest_"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest users cannot update session status"
        )
    
    try:
        session_uuid = uuid.UUID(session_id)
        
        # Получаем сессию
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_uuid,
                ChatSession.user_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Обновляем статус
        session.status = status
        session.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Updated session {session_id} status to {status}")
        return {"success": True, "message": "Session status updated"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session status"
        )

@router.put("/chats/{chat_id}/status")
async def update_chat_status(
    chat_id: str,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление статуса чата"""
    
    # Гостевые пользователи не могут обновлять статус
    if current_user.email.startswith("guest_"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest users cannot update chat status"
        )
    
    try:
        chat_uuid = uuid.UUID(chat_id)
        
        # Проверяем доступ к чату
        result = await db.execute(
            select(Chat, ChatSession).join(
                ChatSession, Chat.session_id == ChatSession.id
            ).where(
                and_(
                    Chat.id == chat_uuid,
                    ChatSession.user_id == current_user.id
                )
            )
        )
        row = result.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found or access denied"
            )
        
        chat, session = row
        
        # Обновляем статус
        chat.status = status
        chat.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Updated chat {chat_id} status to {status}")
        return {"success": True, "message": "Chat status updated"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat status"
        )

# Новые endpoints для работы с восстановлением чатов

@router.get("/users/chats", response_model=List[UserChatsResponse])
async def get_all_user_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех чатов пользователя с группировкой по сессиям"""
    
    # Для гостевых пользователей возвращаем пустой список
    if current_user.email.startswith("guest_"):
        return []
    
    try:
        user_id = str(current_user.id)
        user_chats = await chat_manager.get_all_user_chats(user_id, db=db)
        
        # Преобразуем в Pydantic модели
        response = []
        for session_data in user_chats:
            response.append(UserChatsResponse(
                session_id=session_data["session_id"],
                session_name=session_data["session_name"],
                track_title=session_data["track_title"],
                track_id=session_data["track_id"],
                session_created_at=session_data["session_created_at"],
                chats=session_data["chats"]
            ))
        
        logger.info(f"Retrieved {len(response)} sessions with chats for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting all user chats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user chats"
        )

@router.post("/sessions/{session_id}/switch-chat", response_model=ChatHistoryResponse)
async def switch_to_chat(
    session_id: str,
    switch_request: SwitchChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Переключение на конкретный чат и получение его истории"""
    
    try:
        user_id = str(current_user.id) if not current_user.email.startswith("guest_") else current_user.email
        
        # Переключаемся на выбранный чат
        result = await chat_manager.switch_to_chat(
            session_id=session_id,
            chat_id=switch_request.chat_id,
            user_id=user_id,
            db=db
        )
        
        # Преобразуем в Pydantic модель
        response = ChatHistoryResponse(
            success=result["success"],
            chat_info=result.get("chat_info", {}),
            history=result.get("history", []),
            message_count=result.get("message_count", 0)
        )
        
        logger.info(f"Switched to chat {switch_request.chat_id} with {response.message_count} messages")
        return response
        
    except Exception as e:
        logger.error(f"Error switching to chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to switch to chat"
        )

@router.get("/chats/{chat_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    chat_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение полной истории чата в временной последовательности"""
    
    try:
        user_id = str(current_user.id) if not current_user.email.startswith("guest_") else current_user.email
        
        # Восстанавливаем историю чата
        chat_history = await chat_manager.restore_chat_history(
            session_id=session_id,
            chat_id=chat_id,
            user_id=user_id,
            db=db
        )
        
        # Получаем информацию о чате
        chat_info = {}
        if not current_user.email.startswith("guest_") and db:
            try:
                chat_uuid = uuid.UUID(chat_id)
                result = await db.execute(
                    select(Chat).where(Chat.id == chat_uuid)
                )
                chat = result.scalar_one_or_none()
                
                if chat:
                    chat_info = {
                        "chat_id": str(chat.id),
                        "chat_name": chat.chat_name,
                        "chat_type": chat.chat_type,
                        "status": chat.status,
                        "ai_context": chat.ai_context
                    }
            except Exception as e:
                logger.error(f"Error getting chat info: {e}")
                chat_info = {"chat_id": chat_id, "chat_name": "Chat"}
        
        response = ChatHistoryResponse(
            success=True,
            chat_info=chat_info,
            history=chat_history,
            message_count=len(chat_history)
        )
        
        logger.info(f"Retrieved chat history for {chat_id}: {response.message_count} messages")
        return response
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat ID format"
        )
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat history"
        )

@router.get("/sessions/{session_id}/active-chat")
async def get_active_chat(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Получение ID активного чата для сессии"""
    
    try:
        active_chat_id = chat_manager.get_current_chat_id(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "active_chat_id": active_chat_id,
            "is_active": chat_manager.is_session_active(session_id)
        }
        
    except Exception as e:
        logger.error(f"Error getting active chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active chat"
        )

@router.post("/sessions/{session_id}/restore-existing-chat", response_model=RestoreExistingChatResponse)
async def restore_existing_chat(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Восстановление существующего диалога при возврате пользователя на страницу"""
    
    try:
        user_id = str(current_user.id) if not current_user.email.startswith("guest_") else current_user.email
        
        # Восстанавливаем историю чата
        result = await chat_manager.restore_existing_chat_if_any(
            session_id=session_id,
            user_id=user_id,
            db=db
        )
        
        # Преобразуем в Pydantic модель
        response = RestoreExistingChatResponse(
            success=result["success"],
            has_existing_chat=result["has_existing_chat"],
            chat_id=result.get("chat_id"),
            chat_info=result.get("chat_info"),
            history=result.get("history", []),
            message_count=result.get("message_count", 0)
        )
        
        logger.info(f"Restored existing chat for {session_id}: {response.message_count} messages")
        return response
        
    except Exception as e:
        logger.error(f"Error restoring existing chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore existing chat"
        ) 