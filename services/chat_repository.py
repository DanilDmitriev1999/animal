import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from models.database_models import ChatSession, Chat, ChatMessage, ChatType

class ChatRepository:
    """Data access layer for chat related operations."""

    async def get_active_session(self, user_uuid: uuid.UUID, track_uuid: uuid.UUID, db: AsyncSession):
        result = await db.execute(
            select(ChatSession).where(
                and_(
                    ChatSession.user_id == user_uuid,
                    ChatSession.track_id == track_uuid,
                    ChatSession.status == "active",
                )
            ).order_by(desc(ChatSession.created_at))
        )
        return result.scalar_one_or_none()

    async def create_session(self, user_uuid: uuid.UUID, track_uuid: Optional[uuid.UUID], session_name: str, db: AsyncSession):
        new_session = ChatSession(
            user_id=user_uuid,
            track_id=track_uuid,
            session_name=session_name,
            status="active",
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        return new_session

    async def get_session_by_id(self, session_uuid: uuid.UUID, user_uuid: uuid.UUID, db: AsyncSession):
        result = await db.execute(
            select(ChatSession).where(
                and_(
                    ChatSession.id == session_uuid,
                    ChatSession.user_id == user_uuid,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_chat(self, session_uuid: uuid.UUID, chat_type: ChatType, db: AsyncSession):
        result = await db.execute(
            select(Chat).where(
                and_(
                    Chat.session_id == session_uuid,
                    Chat.chat_type == chat_type,
                    Chat.status == "active",
                )
            ).order_by(desc(Chat.created_at))
        )
        return result.scalar_one_or_none()

    async def create_chat(self, session_uuid: uuid.UUID, chat_name: str, chat_type: ChatType, db: AsyncSession):
        new_chat = Chat(
            session_id=session_uuid,
            chat_name=chat_name,
            chat_type=chat_type,
            status="active",
        )
        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)
        return new_chat

    async def get_chat_by_id(self, chat_uuid: uuid.UUID, db: AsyncSession):
        result = await db.execute(select(Chat).where(Chat.id == chat_uuid))
        return result.scalar_one_or_none()

    async def get_chat_messages(self, chat_uuid: uuid.UUID, db: AsyncSession, limit: int = 50) -> List[ChatMessage]:
        """Returns the most recent chat messages in chronological order."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_id == chat_uuid)
            .order_by(desc(ChatMessage.timestamp))
            .limit(limit)
        )
        rows = result.scalars().all()
        return list(reversed(rows))

    async def save_user_message(self, chat_uuid: uuid.UUID, message: str, message_type: str, db: AsyncSession):
        new_msg = ChatMessage(
            chat_id=chat_uuid,
            sender_type="user",
            message_content=message,
            message_type=message_type,
        )
        db.add(new_msg)
        await db.commit()

    async def save_ai_message(self, chat_uuid: uuid.UUID, message: str, model: str, tokens_used: int, db: AsyncSession):
        new_msg = ChatMessage(
            chat_id=chat_uuid,
            sender_type="ai",
            message_content=message,
            message_type="text",
            ai_model_used=model,
            tokens_used=tokens_used,
        )
        db.add(new_msg)
        await db.commit()
