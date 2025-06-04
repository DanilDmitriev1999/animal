"""
Роутер AI сервиса
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from models.database import get_db
from models.database_models import User, LearningTrack, AIConfiguration
from routers.auth import get_current_user, get_current_user_optional
from services.openai_service import OpenAIService
from utils.config import settings
from services.chat_service import chat_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic модели
class GeneratePlanRequest(BaseModel):
    track_id: str
    user_expectations: str
    session_id: Optional[str] = None
    chat_id: Optional[str] = None

class GeneratePlanResponse(BaseModel):
    success: bool
    plan: Optional[Dict[str, Any]] = None
    chat_id: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None

class ChatRequest(BaseModel):
    message: str
    session_id: str
    track_context: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None

class WelcomeMessageRequest(BaseModel):
    session_id: str
    user_id: str
    skill_area: str
    user_expectations: str
    difficulty_level: str
    duration_hours: int

class WelcomeMessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    chat_id: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None

class FinalizePlanRequest(BaseModel):
    session_id: str
    user_id: str
    skill_area: str
    track_id: str

class FinalizePlanResponse(BaseModel):
    success: bool
    modules_count: Optional[int] = None
    modules: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class LessonRequest(BaseModel):
    lesson_title: str
    module_context: str
    content_type: str = "lecture"

class LessonResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None

class TestConnectionRequest(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None

class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    model_used: Optional[str] = None
    error: Optional[str] = None

class DefaultConfigResponse(BaseModel):
    model_name: str
    base_url: str
    has_custom_key: bool

# Новые модели для работы с модулями
class ModuleLearningRequest(BaseModel):
    track_id: str
    module_id: str
    session_id: str
    user_id: str

class ModuleLearningResponse(BaseModel):
    success: bool
    module_summary: Optional[str] = None
    chat_id: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None

class ModuleChatRequest(BaseModel):
    message: str
    track_id: str
    module_id: str
    session_id: str
    user_id: str
    chat_id: Optional[str] = None

class ModuleChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    chat_id: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None

class ModuleCompleteRequest(BaseModel):
    track_id: str
    module_id: str
    session_id: str
    user_id: str

class ModuleChatHistoryRequest(BaseModel):
    track_id: str
    module_id: str
    session_id: str
    user_id: str
    chat_id: str

class ModuleChatHistoryResponse(BaseModel):
    success: bool
    history: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

async def get_openai_service(current_user: User, db: AsyncSession) -> OpenAIService:
    """Получение OpenAI сервиса для пользователя"""
    
    # Для гостевого пользователя используем настройки по умолчанию
    if current_user.email.startswith("guest_"):
        if not settings.default_openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key not configured"
            )
        
        return OpenAIService(
            api_key=settings.default_openai_api_key,
            base_url=settings.default_openai_base_url,
            model=settings.default_openai_model
        )
    
    # Для зарегистрированных пользователей ищем их настройки AI
    result = await db.execute(
        select(AIConfiguration).where(AIConfiguration.user_id == current_user.id)
    )
    ai_config = result.scalar_one_or_none()
    
    if ai_config and ai_config.api_key_encrypted != "default":
        # Используем пользовательские настройки
        # В продакшене здесь должно быть расшифрование API ключа
        api_key = ai_config.api_key_encrypted
    else:
        # Используем настройки по умолчанию
        api_key = settings.default_openai_api_key
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured"
        )
    
    model = ai_config.model_name if ai_config else settings.default_openai_model
    base_url = ai_config.base_url if ai_config else settings.default_openai_base_url
    
    return OpenAIService(
        api_key=api_key,
        base_url=base_url,
        model=model
    )

@router.post("/generate-plan", response_model=GeneratePlanResponse)
async def generate_plan(
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерация плана курса с помощью AI"""
    
    try:
        # Если это не гостевой пользователь, получаем трек из БД
        if not current_user.email.startswith("guest_"):
            import uuid
            try:
                track_uuid = uuid.UUID(request.track_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid track ID format"
                )
            
            # Получаем трек
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
        else:
            # Для гостевого пользователя создаем заглушку трека
            from models.database_models import DifficultyLevel
            track = type('Track', (), {
                'skill_area': 'Guest Track',
                'difficulty_level': DifficultyLevel.BEGINNER,
                'estimated_duration_hours': 10,
                'user_expectations': request.user_expectations
            })()
        
        # Получаем OpenAI сервис
        openai_service = await get_openai_service(current_user, db)

        chat_id = None
        chat_history = None

        if request.session_id:
            is_guest = current_user.email.startswith("guest_")
            chat_id = request.chat_id or await chat_manager.create_or_get_chat(
                request.session_id,
                "Course Planning",
                "planning",
                db if not is_guest else None,
                str(current_user.id) if current_user.id else "guest"
            )
            chat_history = await chat_manager._get_chat_history(
                chat_id,
                db if not is_guest else None
            )

        # Генерируем план курса с учетом истории
        result = await openai_service.generate_course_plan(
            skill_area=track.skill_area,
            user_expectations=request.user_expectations,
            difficulty_level=track.difficulty_level.value if hasattr(track.difficulty_level, 'value') else str(track.difficulty_level),
            duration_hours=track.estimated_duration_hours,
            chat_history=chat_history
        )
        
        if result["success"]:
            # Пытаемся парсить JSON из ответа
            import json
            try:
                plan_data = json.loads(result["content"])
                
                # Обновляем трек в БД (только для зарегистрированных пользователей)
                if not current_user.email.startswith("guest_") and hasattr(track, 'id'):
                    track.ai_generated_plan = plan_data
                    await db.commit()
                    logger.info(f"Updated track {track.id} with AI generated plan")
                
                if chat_id:
                    if not current_user.email.startswith("guest_"):
                        await chat_manager._save_ai_message_to_db(
                            chat_id,
                            result["content"],
                            openai_service.model,
                            result.get("tokens_used", 0),
                            db
                        )
                    else:
                        chat_manager._save_message_to_guest_history(chat_id, "assistant", result["content"])

                return GeneratePlanResponse(
                    success=True,
                    plan=plan_data,
                    chat_id=chat_id,
                    tokens_used=result.get("tokens_used")
                )
            except json.JSONDecodeError:
                # Если не удалось парсить как JSON, возвращаем как raw response
                logger.warning("Failed to parse AI response as JSON")
                if chat_id:
                    if not current_user.email.startswith("guest_"):
                        await chat_manager._save_ai_message_to_db(
                            chat_id,
                            result["content"],
                            openai_service.model,
                            result.get("tokens_used", 0),
                            db
                        )
                    else:
                        chat_manager._save_message_to_guest_history(chat_id, "assistant", result["content"])

                return GeneratePlanResponse(
                    success=True,
                    plan={"raw_response": result["content"]},
                    chat_id=chat_id,
                    tokens_used=result.get("tokens_used")
                )
        else:
            return GeneratePlanResponse(
                success=False,
                chat_id=chat_id,
                error=result.get("error", "Unknown error")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating plan: {str(e)}")
        return GeneratePlanResponse(
            success=False,
            chat_id=chat_id,
            error=str(e)
        )

@router.post("/chat-response", response_model=ChatResponse)
async def chat_response(
    request: ChatRequest,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Получение ответа AI в чате планирования"""
    
    try:
        # Создаем гостевого пользователя если не аутентифицирован
        if current_user is None:
            from models.database_models import User
            current_user = User(
                id=None,
                email="guest_user",
                first_name="Guest",
                last_name="User",
                role="guest"
            )
            
        # Получаем OpenAI сервис
        openai_service = await get_openai_service(current_user, db)
        
        # Формируем историю сообщений
        messages = [{"role": "user", "content": request.message}]
        
        # Генерируем ответ
        result = await openai_service.generate_chat_response(
            messages=messages,
            context=request.track_context
        )
        
        if result["success"]:
            # Сохраняем сообщения в БД (только для зарегистрированных пользователей)
            if current_user and current_user.id and not current_user.email.startswith("guest_"):
                try:
                    import uuid
                    session_uuid = uuid.UUID(request.session_id)
                    
                    # Проверяем что сессия существует
                    from models.database_models import ChatSession, ChatMessage
                    session_result = await db.execute(
                        select(ChatSession).where(
                            ChatSession.id == session_uuid,
                            ChatSession.user_id == current_user.id
                        )
                    )
                    session = session_result.scalar_one_or_none()
                    
                    if session:
                        # Сохраняем сообщение пользователя
                        user_message = ChatMessage(
                            session_id=session.id,
                            sender_type="user",
                            message_content=request.message,
                            message_type="text"
                        )
                        db.add(user_message)
                        
                        # Сохраняем ответ AI
                        ai_message = ChatMessage(
                            session_id=session.id,
                            sender_type="ai",
                            message_content=result["content"],
                            message_type="text",
                            ai_model_used=openai_service.model
                        )
                        db.add(ai_message)
                        
                        await db.commit()
                        logger.info(f"Saved chat messages for session: {request.session_id}")
                except Exception as e:
                    logger.warning(f"Failed to save chat messages: {str(e)}")
            else:
                logger.info(f"Skipping DB save for guest user or session: {request.session_id}")
            
            return ChatResponse(
                success=True,
                response=result["content"],
                tokens_used=result.get("tokens_used")
            )
        else:
            return ChatResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating chat response: {str(e)}")
        return ChatResponse(
            success=False,
            error=str(e)
        )

@router.post("/generate-lesson", response_model=LessonResponse)
async def generate_lesson_content(
    request: LessonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерация контента для урока"""
    
    try:
        # Получаем OpenAI сервис
        openai_service = await get_openai_service(current_user, db)
        
        # Генерируем контент урока
        result = await openai_service.generate_lesson_content(
            lesson_title=request.lesson_title,
            module_context=request.module_context,
            content_type=request.content_type
        )
        
        if result["success"]:
            return LessonResponse(
                success=True,
                content=result["content"],
                tokens_used=result.get("tokens_used")
            )
        else:
            return LessonResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating lesson content: {str(e)}")
        return LessonResponse(
            success=False,
            error=str(e)
        )

@router.get("/user-config")
async def get_user_ai_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение AI конфигурации пользователя"""
    
    # Для гостевого пользователя возвращаем настройки по умолчанию
    if current_user.email.startswith("guest_"):
        return {
            "model_name": settings.default_openai_model,
            "base_url": settings.default_openai_base_url,
            "max_tokens": 2000,
            "temperature": 0.7,
            "has_custom_key": bool(settings.default_openai_api_key)
        }
    
    # Получаем настройки пользователя
    result = await db.execute(
        select(AIConfiguration).where(AIConfiguration.user_id == current_user.id)
    )
    ai_config = result.scalar_one_or_none()
    
    if ai_config:
        return {
            "model_name": ai_config.model_name,
            "base_url": ai_config.base_url,
            "max_tokens": ai_config.max_tokens,
            "temperature": ai_config.temperature,
            "has_custom_key": ai_config.api_key_encrypted != "default"
        }
    else:
        return {
            "model_name": settings.default_openai_model,
            "base_url": settings.default_openai_base_url,
            "max_tokens": 2000,
            "temperature": 0.7,
            "has_custom_key": False
        }

@router.get("/default-config")
async def get_default_ai_config():
    """Получение AI конфигурации по умолчанию (без аутентификации)"""
    
    return {
        "model_name": settings.default_openai_model,
        "base_url": settings.default_openai_base_url,
        "max_tokens": 2000,
        "temperature": 0.7,
        "has_custom_key": bool(settings.default_openai_api_key)
    }

@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_ai_connection(request: TestConnectionRequest):
    """Тестирование подключения к AI API"""
    
    try:
        # Получаем настройки из запроса или используем по умолчанию
        api_key = request.api_key or settings.default_openai_api_key
        base_url = request.base_url or settings.default_openai_base_url
        model = request.model_name or settings.default_openai_model
        
        if not api_key:
            return TestConnectionResponse(
                success=False,
                error="API ключ не указан"
            )
        
        # Создаем временный OpenAI сервис для тестирования
        test_service = OpenAIService(
            api_key=api_key,
            base_url=base_url,
            model=model
        )
        
        # Делаем простой тестовый запрос
        result = await test_service.generate_chat_response(
            messages=[{"role": "user", "content": "Привет! Это тестовое сообщение."}]
        )
        
        if result["success"]:
            return TestConnectionResponse(
                success=True,
                message="Подключение к AI успешно!",
                model_used=model,
                error=None
            )
        else:
            return TestConnectionResponse(
                success=False,
                message="Ошибка при тестировании подключения",
                model_used=model,
                error=result.get("error", "Ошибка при тестировании подключения")
            )
            
    except Exception as e:
        logger.error(f"Error testing AI connection: {str(e)}")
        return TestConnectionResponse(
            success=False,
            message="Ошибка подключения",
            model_used=model,
            error=f"Ошибка подключения: {str(e)}"
        )

@router.post("/welcome-message", response_model=WelcomeMessageResponse)
async def generate_welcome_message(
    request: WelcomeMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Генерация приветственного сообщения с планом курса через ChatManager"""
    
    try:
        # Создаем/получаем welcome message через ChatManager который создаст единый чат планирования
        result = await chat_manager.send_welcome_message(
            session_id=request.session_id,
            skill_area=request.skill_area,
            user_expectations=request.user_expectations,
            difficulty_level=request.difficulty_level,
            duration_hours=request.duration_hours,
            user_id=request.user_id,
            db=db if current_user and not current_user.email.startswith("guest_") else None
        )
        
        if result["success"]:
            # Извлекаем строку из объекта сообщения если это словарь
            message_content = result["message"]
            if isinstance(message_content, dict):
                message_content = message_content.get("message", "")
            
            return WelcomeMessageResponse(
                success=True,
                message=message_content,
                chat_id=result.get("chat_id"),
                tokens_used=result.get("tokens_used")
            )
        else:
            return WelcomeMessageResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )
            
    except Exception as e:
        logger.error(f"Error generating welcome message: {str(e)}")
        return WelcomeMessageResponse(
            success=False,
            error=str(e)
        )

@router.post("/finalize-course-plan", response_model=FinalizePlanResponse)
async def finalize_course_plan(
    request: FinalizePlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Финализация плана курса и создание модулей через ChatManager"""
    
    try:
        # Используем ChatManager для финализации в том же чате планирования
        result = await chat_manager.finalize_course_plan(
            session_id=request.session_id,
            skill_area=request.skill_area,
            track_id=request.track_id,
            user_id=request.user_id,
            db=db if current_user and not current_user.email.startswith("guest_") else None
        )
        
        if result["success"]:
            return FinalizePlanResponse(
                success=True,
                modules_count=result.get("modules_count"),
                modules=result.get("modules")
            )
        else:
            return FinalizePlanResponse(
                success=False,
                error=result.get("error", "Ошибка финализации плана")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finalizing course plan: {str(e)}")
        return FinalizePlanResponse(
            success=False,
            error=str(e)
        )

@router.post("/module-learning-start", response_model=ModuleLearningResponse)
async def start_module_learning(
    request: ModuleLearningRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Начало изучения модуля - генерация конспекта и создание чата"""
    
    try:
        # Проверяем является ли пользователь гостем
        is_guest = not current_user or current_user.email.startswith("guest_")
        
        # Получаем трек и модуль
        if not is_guest:
            import uuid
            try:
                track_uuid = uuid.UUID(request.track_id)
                # Для модуля может быть числовой ID из тестовых данных
                try:
                    module_uuid = uuid.UUID(request.module_id)
                    use_uuid_module = True
                except ValueError:
                    # Если module_id не UUID, используем его как есть
                    module_uuid = None
                    use_uuid_module = False
                    logger.info(f"Using non-UUID module_id: {request.module_id}")
            except ValueError:
                # Если track_id не UUID, работаем как с гостем
                is_guest = True
                logger.info(f"Non-UUID track_id provided: {request.track_id}, treating as guest")
            
            if not is_guest:
                # Получаем трек из БД
                from sqlalchemy.orm import selectinload
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
                    logger.warning(f"Track {request.track_id} not found for user {current_user.id}")
                    is_guest = True  # Переключаемся в гостевой режим
                else:
                    # Находим модуль
                    module = None
                    if use_uuid_module:
                        for m in track.modules:
                            if m.id == module_uuid:
                                module = m
                                break
                    else:
                        # Ищем по номеру модуля
                        try:
                            module_number = int(request.module_id)
                            for m in track.modules:
                                if m.module_number == module_number:
                                    module = m
                                    break
                        except ValueError:
                            logger.warning(f"Invalid module_id format: {request.module_id}")
                    
                    if not module:
                        logger.warning(f"Module {request.module_id} not found in track {request.track_id}")
                        # Создаем заглушку модуля для продолжения работы
                        module = type('Module', (), {
                            'title': f'Модуль {request.module_id}',
                            'description': 'Модуль курса',
                            'learning_objectives': ['Изучение основ']
                        })()
        
        # Для гостей или если не нашли в БД - используем заглушки
        if is_guest:
            track = type('Track', (), {
                'title': 'Курс обучения',
                'skill_area': 'Общие навыки'
            })()
            module = type('Module', (), {
                'title': f'Модуль {request.module_id}',
                'description': 'Изучение выбранной темы',
                'learning_objectives': ['Освоение новых знаний', 'Практическое применение', 'Закрепление материала']
            })()
        
        # Получаем OpenAI сервис
        openai_service = await get_openai_service(current_user, db)
        
        # Генерируем конспект модуля
        module_summary_prompt = f"""
Создай подробный конспект для модуля "{module.title}" курса "{track.title}".

Информация о модуле:
- Название: {module.title}
- Описание: {getattr(module, 'description', 'Модуль курса')}
- Цели обучения: {getattr(module, 'learning_objectives', ['Изучение основ'])}

Структура конспекта:
1. **Введение** - краткий обзор темы
2. **Основные концепции** - ключевые понятия и определения
3. **Детальное изложение** - подробное объяснение материала
4. **Практические примеры** - конкретные примеры применения
5. **Ключевые моменты** - важные выводы для запоминания
6. **Вопросы для самопроверки** - 3-5 вопросов для закрепления

Требования:
- Используй markdown форматирование
- Добавляй эмодзи для улучшения визуального восприятия
- Структурируй информацию логично и последовательно
- Делай материал понятным и доступным
- Объем: 800-1200 слов

Создай качественный учебный материал который поможет изучить тему эффективно.
"""
        
        # Генерируем конспект
        result = await openai_service.generate_chat_response(
            messages=[{"role": "user", "content": module_summary_prompt}]
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка генерации конспекта: {result.get('error', 'Unknown error')}"
            )
        
        module_summary = result["content"]
        tokens_used = result.get("tokens_used", 0)
        
        # Создаем новый чат для изучения модуля через ChatManager
        chat_result = await chat_manager.create_module_learning_chat(
            session_id=request.session_id,
            track_id=request.track_id,
            module_id=request.module_id,
            user_id=request.user_id,
            module_summary=module_summary,
            db=db if not is_guest else None
        )
        
        if not chat_result["success"]:
            logger.warning(f"Chat creation failed, but continuing: {chat_result.get('error')}")
            # Создаем временный chat_id для продолжения работы
            chat_result = {"success": True, "chat_id": f"temp_chat_{request.session_id}_{request.module_id}"}
        
        logger.info(f"Module learning started for module {request.module_id}, chat_id: {chat_result.get('chat_id')}")
        
        return ModuleLearningResponse(
            success=True,
            module_summary=module_summary,
            chat_id=chat_result.get("chat_id"),
            tokens_used=tokens_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting module learning: {str(e)}")
        return ModuleLearningResponse(
            success=False,
            error=str(e)
        )

@router.post("/module-chat", response_model=ModuleChatResponse)
async def module_chat_response(
    request: ModuleChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Обработка сообщений в чате модуля"""
    
    try:
        # Получаем информацию о треке и модуле для контекста
        context_info = ""
        
        # Только для зарегистрированных пользователей пытаемся работать с БД
        if current_user and not current_user.email.startswith("guest_"):
            import uuid
            try:
                # Пытаемся парсить как UUID
                track_uuid = uuid.UUID(request.track_id)
                module_uuid = uuid.UUID(request.module_id)
                
                # Получаем трек из БД
                from sqlalchemy.orm import selectinload
                result = await db.execute(
                    select(LearningTrack)
                    .options(selectinload(LearningTrack.modules))
                    .where(
                        LearningTrack.id == track_uuid,
                        LearningTrack.user_id == current_user.id
                    )
                )
                track = result.scalar_one_or_none()
                
                if track:
                    # Находим модуль
                    module = None
                    for m in track.modules:
                        if m.id == module_uuid:
                            module = m
                            break
                    
                    if module:
                        context_info = f"Трек: {track.title}\nМодуль: {module.title}\nОписание: {getattr(module, 'description', '')}"
                        
            except (ValueError, TypeError) as e:
                # ID не в формате UUID - работаем как с гостем, но логируем для диагностики
                logger.info(f"Non-UUID track/module ID for user {current_user.email}: track_id={request.track_id}, module_id={request.module_id}")
                # Не поднимаем ошибку, просто продолжаем без контекста из БД
        
        # Обрабатываем сообщение через ChatManager
        result = await chat_manager.process_module_chat_message(
            session_id=request.session_id,
            chat_id=request.chat_id,
            user_message=request.message,
            user_id=request.user_id,
            track_context=context_info,
            db=db if current_user and not current_user.email.startswith("guest_") else None
        )
        
        if result["success"]:
            return ModuleChatResponse(
                success=True,
                response=result["response"],
                chat_id=result.get("chat_id"),
                tokens_used=result.get("tokens_used")
            )
        else:
            return ModuleChatResponse(
                success=False,
                error=result.get("error", "Ошибка обработки сообщения"),
                chat_id=request.chat_id
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing module chat message: {str(e)}")
        return ModuleChatResponse(
            success=False,
            error=str(e),
            chat_id=request.chat_id
        )

@router.post("/module-complete")
async def complete_module(
    request: ModuleCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Завершение изучения модуля"""
    
    try:
        result = await chat_manager.complete_module(
            session_id=request.session_id,
            track_id=request.track_id,
            module_id=request.module_id,
            user_id=request.user_id,
            db=db if current_user and not current_user.email.startswith("guest_") else None
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error completing module: {str(e)}")
        return {"success": False, "error": str(e)}

@router.post("/module-chat-history", response_model=ModuleChatHistoryResponse)
async def get_module_chat_history(
    request: ModuleChatHistoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Получение истории чата модуля"""
    
    try:
        # Получаем историю чата модуля из БД
        result = await chat_manager.get_module_chat_history(
            session_id=request.session_id,
            track_id=request.track_id,
            module_id=request.module_id,
            user_id=request.user_id,
            db=db if current_user and not current_user.email.startswith("guest_") else None
        )
        
        if result["success"]:
            return ModuleChatHistoryResponse(
                success=True,
                history=result["history"],
                error=None
            )
        else:
            return ModuleChatHistoryResponse(
                success=False,
                error=result.get("error", "Ошибка получения истории чата")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting module chat history: {str(e)}")
        return ModuleChatHistoryResponse(
            success=False,
            error=str(e)
        ) 