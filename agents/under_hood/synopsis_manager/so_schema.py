from __future__ import annotations

from typing import Literal, Optional, Union
from pydantic import BaseModel, Field

# AICODE-NOTE: Переиспользуем анкету из планировщика
from ..learning_planner.so_schema import CreateTrackParams


# --- Synopsis item types -----------------------------------------------------


class HeadingItem(BaseModel):
    type: Literal["heading"] = "heading"
    text: str


class TextItem(BaseModel):
    type: Literal["text"] = "text"
    text: str


class DefinitionItem(BaseModel):
    type: Literal["definition"] = "definition"
    term: str
    description: str


class CodeItem(BaseModel):
    type: Literal["code"] = "code"
    language: Optional[str] = None
    code: str


class NoteItem(BaseModel):
    type: Literal["note"] = "note"
    text: str


class ListItem(BaseModel):
    type: Literal["list"] = "list"
    items: list[str]


SynopsisItem = Union[HeadingItem, TextItem, DefinitionItem, CodeItem, NoteItem, ListItem]


class SynopsisSO(BaseModel):
    """Результат агента-конспекта.

    - items: список элементов конспекта, совместимых с фронтом `LiveSynopsis`
    - lastUpdated: строка-временная отметка в локальном часовом поясе (UI может заменить)
    """

    items: list[SynopsisItem] = Field(default_factory=list)
    lastUpdated: str


# --- LLM-friendly schema (простая и детально описанная) ---------------------


class LLMSynopsisItem(BaseModel):
    """Упрощённая форма элемента конспекта для LLM.

    Правила заполнения по `type`:
    - type="heading": заполни только `text` — короткий заголовок раздела.
    - type="text": заполни только `text` — 1–2 предложения.
    - type="definition": заполни `term` и `description` — чёткое определение термина.
    - type="list": заполни `items` — массив коротких пунктов (строк).
    - type="code": заполни `code` и, опционально, `language` (например, "python").
    - type="note": заполни только `text` — краткая заметка/совет.

    Не добавляй лишние поля. Для каждого элемента указывай только те ключи,
    которые допускаются для данного `type`.
    """

    type: Literal["heading", "text", "definition", "list", "code", "note"] = Field(
        ..., description="Тип элемента конспекта"
    )
    text: Optional[str] = Field(
        default=None,
        description="Текст для heading|text|note. Короткая фраза или 1–2 предложения.",
    )
    term: Optional[str] = Field(default=None, description="Термин для definition")
    description: Optional[str] = Field(
        default=None, description="Определение термина для definition"
    )
    items: Optional[list[str]] = Field(
        default=None, description="Список пунктов для list (каждый — короткая строка)"
    )
    code: Optional[str] = Field(default=None, description="Фрагмент кода для code")
    language: Optional[str] = Field(
        default=None, description="Язык кода для code (например, 'python')"
    )


class SynopsisLLMSchema(BaseModel):
    """Упрощённая итоговая схема для LLM.

    Требуемый формат ответа:
    {
      "items": [ { "type": "heading", "text": "..." }, ... ],
      "lastUpdated": "YYYY-MM-DD HH:MM"  // опционально, можно опустить
    }

    Если не можешь вычислить `lastUpdated`, просто не указывай его.
    """

    items: list[LLMSynopsisItem] = Field(
        default_factory=list,
        description="Список элементов конспекта. 12–24 элемента — хорошая длина.",
    )
    lastUpdated: Optional[str] = Field(
        default=None,
        description="Отметка времени, опционально. Формат YYYY-MM-DD HH:MM",
    )


class CreateSynopsisInput(BaseModel):
    """Вход для создания конспекта по анкете и роадмапу."""

    action: Literal["create"] = "create"
    params: CreateTrackParams
    plan: list[str] = Field(default_factory=list)


class UpdateSynopsisInput(BaseModel):
    """Вход для обновления существующего конспекта на основе правок и плана."""

    action: Literal["update"] = "update"
    params: CreateTrackParams
    plan: list[str] = Field(default_factory=list)
    synopsis: list[SynopsisItem] = Field(default_factory=list)
    instructions: Optional[str] = Field(
        default=None,
        description="Свободный текст с правками пользователя, приоритетнее плана",
    )


 