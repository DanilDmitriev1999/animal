"""
// AICODE-NOTE: Реестр фабрик агентов и инструментов + загрузчик YAML-промптов.
"""

from __future__ import annotations

from typing import Callable, Dict, Tuple, Protocol, Any, Optional
import os

try:  # pragma: no cover - опциональная зависимость
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


class SupportsMemory(Protocol):
    # AICODE-NOTE: Протокол совместим с BaseMemory
    async def load_dialog(self, session_id: str, role_policy: dict) -> list[dict]: ...
    async def append(self, session_id: str, messages: list[dict]) -> None: ...


AgentFactory = Callable[..., Any]
ToolFactory = Callable[..., Any]

_AGENT_FACTORIES: Dict[Tuple[str, str], AgentFactory] = {}
_TOOL_FACTORIES: Dict[Tuple[str, str], ToolFactory] = {}


def register_agent(id: str, version: str):
    """Декоратор для регистрации фабрики агента."""

    def deco(factory: AgentFactory) -> AgentFactory:
        _AGENT_FACTORIES[(id, version)] = factory
        return factory

    return deco


def get_agent(id: str, version: str, /, **factory_kwargs: Any) -> Any:
    key = (id, version)
    if key not in _AGENT_FACTORIES:
        raise KeyError(f"Agent factory not found: {id}@{version}")
    return _AGENT_FACTORIES[key](**factory_kwargs)


def register_tool(id: str, version: str):
    """Декоратор для регистрации фабрики инструмента."""

    def deco(factory: ToolFactory) -> ToolFactory:
        _TOOL_FACTORIES[(id, version)] = factory
        return factory

    return deco


def get_tool(id: str, version: str, /, **factory_kwargs: Any) -> Any:
    key = (id, version)
    if key not in _TOOL_FACTORIES:
        raise KeyError(f"Tool factory not found: {id}@{version}")
    return _TOOL_FACTORIES[key](**factory_kwargs)


# --- Prompt Registry (YAML) -------------------------------------------------

_PROMPTS: Dict[Tuple[str, str], str] = {}
_LATEST: Dict[str, str] = {}


def _ensure_yaml_available() -> None:
    if yaml is None:
        raise RuntimeError("PyYAML не установлен. Добавьте 'pyyaml' в зависимости.")


def _load_yaml_file(path: str) -> None:
    _ensure_yaml_available()
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    prompt_id: Optional[str] = data.get("id")
    versions: dict = data.get("versions", {})
    if not prompt_id or not isinstance(versions, dict) or not versions:
        return
    last_version: Optional[str] = None
    for ver, text in versions.items():
        if not isinstance(ver, str) or not isinstance(text, str):
            continue
        _PROMPTS[(prompt_id, ver)] = text
        last_version = ver
    if last_version:
        _LATEST[prompt_id] = last_version


def _scan_prompts_directory(base_dir: str) -> None:
    if not os.path.isdir(base_dir):
        return
    for name in os.listdir(base_dir):
        if name.endswith(".yaml"):
            _load_yaml_file(os.path.join(base_dir, name))


def _scan_under_hood_prompts(agents_dir: str) -> None:
    under_hood_dir = os.path.join(agents_dir, "under_hood")
    if not os.path.isdir(under_hood_dir):
        return
    for entry in os.listdir(under_hood_dir):
        sub = os.path.join(under_hood_dir, entry)
        if os.path.isdir(sub):
            for name in os.listdir(sub):
                if name.endswith(".yaml"):
                    _load_yaml_file(os.path.join(sub, name))


def autodiscover_prompts() -> None:
    # Без pyyaml — тихая деградация
    if yaml is None:  # type: ignore
        return
    _PROMPTS.clear()
    _LATEST.clear()
    agents_dir = os.path.dirname(__file__)
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    _scan_prompts_directory(prompts_dir)
    _scan_under_hood_prompts(os.path.dirname(__file__))


def get_prompt(prompt_id: str, version: Optional[str] = None) -> str:
    if version is None:
        if prompt_id not in _LATEST:
            raise KeyError(f"Prompt id not found or not loaded: {prompt_id}")
        version = _LATEST[prompt_id]
    key = (prompt_id, version)
    if key not in _PROMPTS:
        raise KeyError(f"Prompt not found: {prompt_id}@{version}")
    return _PROMPTS[key]


__all__ = [
    "register_agent",
    "get_agent",
    "register_tool",
    "get_tool",
    "autodiscover_prompts",
    "get_prompt",
]


