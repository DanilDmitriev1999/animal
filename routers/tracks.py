"""
Роутер учебных треков
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from models.database import get_db
from models.database_models import User, LearningTrack, DifficultyLevel, TrackStatus, ChatSession, Chat, ChatMessage, CourseModule, Lesson, HomeworkAssignment
from routers.auth import get_current_user
from services.openai_service import create_openai_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic модели
class ModuleResponse(BaseModel):
    id: str
    module_number: int
    title: str
    description: str
    learning_objectives: List[str]
    estimated_duration_hours: int
    status: str
    ai_generated_content: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

class TrackCreate(BaseModel):
    title: str
    description: str
    skill_area: str
    difficulty_level: str
    estimated_duration_hours: int
    user_expectations: str

class TrackUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    skill_area: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration_hours: Optional[int] = None
    user_expectations: Optional[str] = None
    status: Optional[str] = None

class TrackResponse(BaseModel):
    id: str
    title: str
    description: str
    skill_area: str
    difficulty_level: str
    estimated_duration_hours: int
    status: str
    user_expectations: str
    ai_generated_plan: Optional[dict] = None
    modules: List[ModuleResponse] = []  # Добавляем модули в ответ
    created_at: datetime
    updated_at: datetime

@router.get("", response_model=List[TrackResponse])
async def get_tracks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка треков пользователя с модулями"""
    
    # Для гостевого пользователя возвращаем пустой список
    if current_user.email.startswith("guest_"):
        return []
    
    # Получаем треки пользователя из БД с загрузкой модулей
    result = await db.execute(
        select(LearningTrack)
        .options(selectinload(LearningTrack.modules))
        .where(LearningTrack.user_id == current_user.id)
    )
    tracks = result.scalars().all()
    
    # Конвертируем в модели ответа
    track_responses = []
    for track in tracks:
        # Загружаем модули для трека
        modules = []
        if track.modules:
            modules = [
                ModuleResponse(
                    id=str(module.id),
                    module_number=module.module_number,
                    title=module.title,
                    description=module.description or "",
                    learning_objectives=module.learning_objectives or [],
                    estimated_duration_hours=module.estimated_duration_hours or 0,
                    status=module.status or "not_started",
                    ai_generated_content=module.ai_generated_content,
                    created_at=module.created_at,
                    updated_at=module.updated_at
                )
                for module in sorted(track.modules, key=lambda m: m.module_number)
            ]
        
        track_response = TrackResponse(
            id=str(track.id),
            title=track.title,
            description=track.description or "",
            skill_area=track.skill_area or "",
            difficulty_level=track.difficulty_level.value,
            estimated_duration_hours=track.estimated_duration_hours or 0,
            status=track.status.value,
            user_expectations=track.user_expectations or "",
            ai_generated_plan=track.ai_generated_plan,
            modules=modules,  # Включаем модули в ответ
            created_at=track.created_at,
            updated_at=track.updated_at
        )
        track_responses.append(track_response)
    
    logger.info(f"Retrieved {len(track_responses)} tracks with modules for user {current_user.id}")
    return track_responses

@router.post("", response_model=TrackResponse)
async def create_track(
    track_data: TrackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового трека"""
    
    try:
        # Валидируем уровень сложности
        try:
            difficulty = DifficultyLevel(track_data.difficulty_level.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid difficulty level. Must be: beginner, intermediate, or advanced"
            )
        
        # Для гостевого пользователя создаем временный ID
        user_id = current_user.id if not current_user.email.startswith("guest_") else uuid.uuid4()
        
        # Создаем новый трек
        new_track = LearningTrack(
            user_id=user_id,
            title=track_data.title,
            description=track_data.description,
            skill_area=track_data.skill_area,
            difficulty_level=difficulty,
            estimated_duration_hours=track_data.estimated_duration_hours,
            user_expectations=track_data.user_expectations,
            status=TrackStatus.PLANNING
        )
        
        # Для гостевых пользователей устанавливаем ID и временные метки вручную
        if current_user.email.startswith("guest_"):
            new_track.id = uuid.uuid4()
            new_track.created_at = datetime.utcnow()
            new_track.updated_at = datetime.utcnow()
        
        # Сохраняем в БД (только для зарегистрированных пользователей)
        if not current_user.email.startswith("guest_"):
            db.add(new_track)
            await db.commit()
            await db.refresh(new_track)
        
        # Убираем автоматическую генерацию AI плана при создании трека
        # План будет генерироваться в welcome-message, чтобы избежать дублирования
        
        # Формируем ответ
        track_response = TrackResponse(
            id=str(new_track.id),
            title=new_track.title,
            description=new_track.description or "",
            skill_area=new_track.skill_area or "",
            difficulty_level=new_track.difficulty_level.value,
            estimated_duration_hours=new_track.estimated_duration_hours or 0,
            status=new_track.status.value,
            user_expectations=new_track.user_expectations or "",
            ai_generated_plan=new_track.ai_generated_plan,  # Будет None изначально
            created_at=new_track.created_at,
            updated_at=new_track.updated_at
        )
        
        logger.info(f"Created track: {new_track.title} for user {user_id}")
        return track_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating track: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create track"
        )

@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение деталей трека с модулями"""
    
    # Для гостей просто возвращаем заглушку
    if current_user.email.startswith("guest_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found for guest user"
        )
    
    try:
        track_uuid = uuid.UUID(track_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track ID format"
        )
    
    # Получаем трек из БД с загрузкой модулей
    result = await db.execute(
        select(LearningTrack)
        .options(selectinload(LearningTrack.modules))
        .where(
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
    
    # Загружаем модули для трека
    modules = []
    if track.modules:
        modules = [
            ModuleResponse(
                id=str(module.id),
                module_number=module.module_number,
                title=module.title,
                description=module.description or "",
                learning_objectives=module.learning_objectives or [],
                estimated_duration_hours=module.estimated_duration_hours or 0,
                status=module.status or "not_started",
                ai_generated_content=module.ai_generated_content,
                created_at=module.created_at,
                updated_at=module.updated_at
            )
            for module in sorted(track.modules, key=lambda m: m.module_number)
        ]
    
    # Формируем ответ
    track_response = TrackResponse(
        id=str(track.id),
        title=track.title,
        description=track.description or "",
        skill_area=track.skill_area or "",
        difficulty_level=track.difficulty_level.value,
        estimated_duration_hours=track.estimated_duration_hours or 0,
        status=track.status.value,
        user_expectations=track.user_expectations or "",
        ai_generated_plan=track.ai_generated_plan,
        modules=modules,  # Включаем модули в ответ
        created_at=track.created_at,
        updated_at=track.updated_at
    )
    
    return track_response

@router.put("/{track_id}", response_model=TrackResponse)
async def update_track(
    track_id: str,
    track_update: TrackUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление трека"""
    
    # Для гостей не поддерживаем обновление
    if current_user.email.startswith("guest_"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Track update not supported for guest users"
        )
    
    try:
        track_uuid = uuid.UUID(track_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track ID format"
        )
    
    # Получаем трек из БД с загрузкой модулей для обновления
    result = await db.execute(
        select(LearningTrack)
        .options(selectinload(LearningTrack.modules))
        .where(
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
    
    # Обновляем поля
    update_data = track_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "difficulty_level" and value:
            try:
                track.difficulty_level = DifficultyLevel(value.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid difficulty level"
                )
        elif field == "status" and value:
            try:
                track.status = TrackStatus(value.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status"
                )
        else:
            setattr(track, field, value)
    
    # Сохраняем изменения
    await db.commit()
    await db.refresh(track)
    
    # Загружаем модули для обновленного трека
    modules = []
    if track.modules:
        modules = [
            ModuleResponse(
                id=str(module.id),
                module_number=module.module_number,
                title=module.title,
                description=module.description or "",
                learning_objectives=module.learning_objectives or [],
                estimated_duration_hours=module.estimated_duration_hours or 0,
                status=module.status or "not_started",
                ai_generated_content=module.ai_generated_content,
                created_at=module.created_at,
                updated_at=module.updated_at
            )
            for module in sorted(track.modules, key=lambda m: m.module_number)
        ]
    
    # Формируем ответ
    track_response = TrackResponse(
        id=str(track.id),
        title=track.title,
        description=track.description or "",
        skill_area=track.skill_area or "",
        difficulty_level=track.difficulty_level.value,
        estimated_duration_hours=track.estimated_duration_hours or 0,
        status=track.status.value,
        user_expectations=track.user_expectations or "",
        ai_generated_plan=track.ai_generated_plan,
        modules=modules,  # Включаем модули в ответ
        created_at=track.created_at,
        updated_at=track.updated_at
    )
    
    logger.info(f"Updated track: {track.title}")
    return track_response

@router.delete("/{track_id}")
async def delete_track(
    track_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление трека"""
    
    # Для гостей не поддерживаем удаление из БД, только уведомляем об успехе
    if current_user.email.startswith("guest_"):
        logger.info(f"Guest user attempting to delete track: {track_id}")
        return {"success": True, "message": "Track deleted successfully"}
    
    try:
        track_uuid = uuid.UUID(track_id)
    except ValueError:
        logger.error(f"Invalid track ID format: {track_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track ID format"
        )
    
    # Получаем трек из БД
    result = await db.execute(
        select(LearningTrack).where(
            LearningTrack.id == track_uuid,
            LearningTrack.user_id == current_user.id
        )
    )
    track = result.scalar_one_or_none()
    
    if not track:
        logger.warning(f"Track not found: {track_id} for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    try:
        # Удаляем связанные данные сначала, чтобы избежать ошибок foreign key
        
        # 1. Удаляем чат сессии и связанные данные
        
        # Получаем все чат сессии для этого трека
        chat_sessions_result = await db.execute(
            select(ChatSession).where(ChatSession.track_id == track_uuid)
        )
        chat_sessions = chat_sessions_result.scalars().all()
        
        for session in chat_sessions:
            # Удаляем чаты и сообщения сессии
            chats_result = await db.execute(
                select(Chat).where(Chat.session_id == session.id)
            )
            chats = chats_result.scalars().all()
            
            for chat in chats:
                # Удаляем сообщения чата
                messages_result = await db.execute(
                    select(ChatMessage).where(ChatMessage.chat_id == chat.id)
                )
                messages = messages_result.scalars().all()
                for message in messages:
                    await db.delete(message)
                
                # Удаляем чат
                await db.delete(chat)
            
            # Удаляем сессию
            await db.delete(session)
        
        # 2. Удаляем модули курса и связанные данные
        modules_result = await db.execute(
            select(CourseModule).where(CourseModule.track_id == track_uuid)
        )
        modules = modules_result.scalars().all()
        
        for module in modules:
            # Удаляем уроки модуля
            lessons_result = await db.execute(
                select(Lesson).where(Lesson.module_id == module.id)
            )
            lessons = lessons_result.scalars().all()
            
            for lesson in lessons:
                # Удаляем домашние задания урока
                homework_result = await db.execute(
                    select(HomeworkAssignment).where(HomeworkAssignment.lesson_id == lesson.id)
                )
                homework_assignments = homework_result.scalars().all()
                for homework in homework_assignments:
                    await db.delete(homework)
                
                # Удаляем урок
                await db.delete(lesson)
            
            # Удаляем модуль
            await db.delete(module)
        
        # 3. Теперь можно безопасно удалить трек
        await db.delete(track)
        await db.commit()
        
        logger.info(f"Successfully deleted track: {track.title} (ID: {track.id}) and all related data for user {current_user.id}")
        
        return {"success": True, "message": "Track deleted successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting track {track.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete track: {str(e)}"
        ) 