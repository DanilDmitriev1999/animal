from typing import Literal
from pydantic import BaseModel


class PlanSO(BaseModel):
    """Структура итогового плана, возвращаемого агентом.

    - modules: перечисление названий модулей (короткие, 1 строка)
    """

    modules: list[str]


class CreateTrackParams(BaseModel):
    """Входные параметры шага 1 создания трека (см. фронт `/tracks/create`)."""

    title: str
    description: str
    goal: str
    focus: Literal["theory", "practice"] = "theory"
    tone: Literal["strict", "friendly", "motivational", "neutral"] = "friendly"
