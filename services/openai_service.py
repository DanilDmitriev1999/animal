"""
Сервис для работы с OpenAI API
"""
from openai import AsyncOpenAI
from typing import Dict, Any, Optional, List
import logging
from utils.config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self, api_key: str, base_url: str = None, model: str = None):
        self.api_key = api_key
        self.base_url = base_url or settings.default_openai_base_url
        self.model = model or settings.default_openai_model
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def generate_welcome_plan_message(self, 
                                          skill_area: str, 
                                          user_expectations: str,
                                          difficulty_level: str,
                                          duration_hours: int) -> Dict[str, Any]:
        """Генерирует приветственное сообщение с планом курса"""

        prompt = f"""
        Привет! Я твой AI-помощник для планирования обучения. 

        Ты создал трек по изучению: **{skill_area}**

        На основе твоих данных:
        - Уровень сложности: {difficulty_level}
        - Планируемое время: {duration_hours} часов
        - Твои ожидания: {user_expectations}

        Я подготовил для тебя детальный план обучения! 📚

        ## 🎯 Предлагаемый план курса:

        Создай красивый структурированный план курса с использованием эмодзи и markdown разметки.
        Включи:
        1. **Цели обучения** (2-3 основные цели)
        2. **Структура курса** (4-6 модулей с названиями и кратким описанием)
        3. **Практические проекты** (2-3 проекта для закрепления)
        4. **Рекомендации по изучению**

        В конце спроси пользователя:
        - Нравится ли ему план?
        - Что хотел бы изменить или дополнить?
        - Готов ли финализировать план для создания модулей?

        Используй дружелюбный тон, эмодзи и структурированную подачу информации.
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты дружелюбный AI-куратор образовательных курсов. Создаешь мотивирующие и структурированные планы обучения с красивым оформлением."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )

            content = response.choices[0].message.content
            logger.info(f"Generated welcome plan message for {skill_area}")

            return {
                "success": True,
                "content": content,
                "tokens_used": response.usage.total_tokens
            }

        except Exception as e:
            logger.error(f"Error generating welcome plan message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_course_plan(self, 
                                 skill_area: str, 
                                 user_expectations: str,
                                 difficulty_level: str,
                                 duration_hours: int) -> Dict[str, Any]:
        """Генерирует план курса на основе пожеланий пользователя"""

        prompt = f"""
        Создай детальный план курса для изучения навыка: {skill_area}

        Параметры:
        - Уровень сложности: {difficulty_level}
        - Планируемая продолжительность: {duration_hours} часов
        - Ожидания пользователя: {user_expectations}

        Создай структурированный план в JSON формате со следующими разделами:
        1. Общее описание курса
        2. Цели обучения
        3. Модули курса (3-7 модулей)
        4. Для каждого модуля: название, описание, продолжительность, темы
        5. Практические задания
        6. Финальный проект

        Отвечай только в JSON формате без дополнительного текста.
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты экспертный куратор образовательных курсов. Создаешь детальные планы обучения."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            logger.info(f"Generated course plan for {skill_area}")

            return {
                "success": True,
                "content": content,
                "tokens_used": response.usage.total_tokens
            }

        except Exception as e:
            logger.error(f"Error generating course plan: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_finalized_modules(self, 
                                       course_plan: str,
                                       skill_area: str) -> Dict[str, Any]:
        """Генерирует финализированные модули курса с названиями и описаниями"""

        prompt = f"""
На основе плана курса по изучению: {skill_area}

План курса:
{course_plan}

Создай JSON список модулей курса для сохранения в базе данных.

ВАЖНО: Отвечай ТОЛЬКО в формате JSON массива, без дополнительного текста или разметки.

Формат должен быть точно такой:
[
  {{
    "module_number": 1,
    "title": "Название модуля",
    "description": "Краткое описание модуля (2-3 предложения)",
    "estimated_duration_hours": 5,
    "learning_objectives": ["Цель 1", "Цель 2", "Цель 3"],
    "status": "not_started"
  }},
  {{
    "module_number": 2,
    "title": "Следующий модуль",
    "description": "Описание следующего модуля",
    "estimated_duration_hours": 6,
    "learning_objectives": ["Цель 1", "Цель 2"],
    "status": "not_started"
  }}
]

Требования:
- Количество модулей: 4-6
- Модули должны быть логически связаны и покрывать весь план обучения
- Каждый модуль должен иметь все указанные поля
- estimated_duration_hours должно быть числом от 3 до 12
- learning_objectives - массив строк с 2-4 целями
- status всегда "not_started"
- Отвечай только JSON, без ```json``` или других обёрток
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты создаешь структурированные модули курсов строго в JSON формате. Отвечай только валидным JSON массивом без дополнительного текста."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Низкая температура для более стабильного JSON
                max_tokens=1500
            )

            content = response.choices[0].message.content.strip()
            
            # Очищаем возможные markdown обёртки
            if content.startswith('```'):
                content = content.split('\n', 1)[1]
            if content.endswith('```'):
                content = content.rsplit('\n', 1)[0]
            content = content.strip()
            
            # Проверяем что это валидный JSON
            import json
            try:
                parsed_modules = json.loads(content)
                if not isinstance(parsed_modules, list):
                    raise ValueError("Response is not a JSON array")
                
                # Валидируем структуру каждого модуля
                for i, module in enumerate(parsed_modules):
                    if not isinstance(module, dict):
                        raise ValueError(f"Module {i} is not a JSON object")
                    
                    required_fields = ["module_number", "title", "description", "estimated_duration_hours", "learning_objectives", "status"]
                    for field in required_fields:
                        if field not in module:
                            module[field] = self._get_default_field_value(field, i + 1)
                
                logger.info(f"Generated {len(parsed_modules)} finalized modules for {skill_area}")
                
                return {
                    "success": True,
                    "content": json.dumps(parsed_modules, ensure_ascii=False, indent=2),
                    "tokens_used": response.usage.total_tokens
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Invalid JSON in AI response: {e}")
                logger.error(f"AI response content: {content[:500]}...")
                
                # Fallback: создаем базовые модули
                fallback_modules = self._create_fallback_modules(skill_area, course_plan)
                return {
                    "success": True,
                    "content": json.dumps(fallback_modules, ensure_ascii=False, indent=2),
                    "tokens_used": response.usage.total_tokens,
                    "warning": "Used fallback modules due to JSON parsing error"
                }

        except Exception as e:
            logger.error(f"Error generating finalized modules: {str(e)}")
            
            # Fallback: создаем базовые модули
            fallback_modules = self._create_fallback_modules(skill_area, course_plan)
            return {
                "success": True,
                "content": json.dumps(fallback_modules, ensure_ascii=False, indent=2),
                "tokens_used": 0,
                "warning": f"Used fallback modules due to error: {str(e)}"
            }
    
    def _get_default_field_value(self, field: str, module_number: int):
        """Возвращает значение по умолчанию для поля модуля"""
        defaults = {
            "module_number": module_number,
            "title": f"Модуль {module_number}",
            "description": "Описание модуля",
            "estimated_duration_hours": 5,
            "learning_objectives": ["Изучение основ", "Практические навыки"],
            "status": "not_started"
        }
        return defaults.get(field, "")
    
    def _create_fallback_modules(self, skill_area: str, course_plan: str):
        """Создает базовые модули как fallback"""
        modules = []
        
        # Извлекаем ключевые темы из плана
        plan_lines = course_plan.split('\n')
        topics = []
        for line in plan_lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                topic = line[1:].strip()
                if len(topic) > 5 and len(topic) < 100:
                    topics.append(topic)
        
        # Создаем модули на основе тем или используем базовые
        if len(topics) >= 3:
            selected_topics = topics[:min(5, len(topics))]
        else:
            selected_topics = [
                f"Введение в {skill_area}",
                f"Основы {skill_area}",
                f"Практическое применение",
                f"Продвинутые техники",
                f"Финальный проект"
            ]
        
        for i, topic in enumerate(selected_topics):
            modules.append({
                "module_number": i + 1,
                "title": topic,
                "description": f"Изучение темы: {topic}. Практические задания и теоретический материал.",
                "estimated_duration_hours": 5 + (i % 3),  # 5-7 часов
                "learning_objectives": [
                    f"Понимание {topic.lower()}",
                    "Практические навыки",
                    "Применение знаний"
                ],
                "status": "not_started"
            })
        
        return modules

    async def generate_chat_response(self, 
                                   messages: List[Dict[str, str]], 
                                   context: str = None) -> Dict[str, Any]:
        """Генерирует ответ в чате для планирования курса"""

        system_prompt = """
        Ты помощник для планирования образовательных курсов. 
        Помогаешь пользователям создавать и корректировать планы обучения.

        Твои задачи:
        1. Обсуждать детали курса с пользователем
        2. Предлагать улучшения и корректировки
        3. Отвечать на вопросы о структуре курса
        4. Помогать финализировать план

        Будь дружелюбным, конструктивным и профессиональным.
        """

        if context:
            system_prompt += f"\n\nКонтекст курса: {context}"

        try:
            full_messages = [{"role": "system", "content": system_prompt}] + messages

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=0.8,
                max_tokens=1000
            )

            content = response.choices[0].message.content

            return {
                "success": True,
                "content": content,
                "tokens_used": response.usage.total_tokens
            }

        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_lesson_content(self, 
                                    lesson_title: str,
                                    module_context: str,
                                    content_type: str) -> Dict[str, Any]:
        """Генерирует контент для урока"""

        prompt = f"""
        Создай {content_type} для урока "{lesson_title}"

        Контекст модуля: {module_context}

        Требования:
        - Структурированный материал
        - Практические примеры  
        - Четкие объяснения
        - Задания для закрепления (если применимо)

        Формат ответа: markdown
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты опытный преподаватель, создающий качественные образовательные материалы."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=1500
            )

            content = response.choices[0].message.content

            return {
                "success": True,
                "content": content,
                "tokens_used": response.usage.total_tokens
            }

        except Exception as e:
            logger.error(f"Error generating lesson content: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Фабрика для создания OpenAI сервиса
async def create_openai_service(user_id: str) -> Optional[OpenAIService]:
    """Создает OpenAI сервис на основе настроек пользователя"""
    # Здесь должна быть логика получения настроек AI пользователя из БД
    # Для примера используем настройки по умолчанию

    api_key = settings.default_openai_api_key
    if not api_key:
        logger.error("OpenAI API key not configured")
        return None

    return OpenAIService(
        api_key=api_key,
        base_url=settings.default_openai_base_url,
        model=settings.default_openai_model
    )
