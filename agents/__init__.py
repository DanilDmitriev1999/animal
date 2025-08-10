"""
// AICODE-NOTE: Пакет агентов. Загрузка .env и автодискавери реализаций.
"""

from __future__ import annotations

import os
import pkgutil
import importlib


from dotenv import load_dotenv  # type: ignore

load_dotenv()


# Публичное API реестра
from .registry import (  # noqa: E402
    register_agent,
    get_agent,
    register_tool,
    get_tool,
)

# Публичное API реестра промптов (встроен в registry)
from .registry import (  # noqa: E402
    autodiscover_prompts,
    get_prompt,
)


def autodiscover() -> None:
    """Импортировать все подпакеты `under_hood.*` для активации декораторов."""
    base_pkg = __name__ + ".under_hood"
    try:
        pkg = importlib.import_module(base_pkg)
    except ModuleNotFoundError:
        return

    for mod in pkgutil.walk_packages(pkg.__path__, prefix=base_pkg + "."):
        importlib.import_module(mod.name)


__all__ = [
    "register_agent",
    "get_agent",
    "register_tool",
    "get_tool",
    "autodiscover",
    "load_env",
    "autodiscover_prompts",
    "get_prompt",
]