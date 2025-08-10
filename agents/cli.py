"""
// AICODE-NOTE: Простой CLI для регистрации и запуска агентов (симуляция бэкенда).

Примеры:
  python -m agents.cli list
  python -m agents.cli run learning_planner v1 --session s1 --topic "Python"
"""

from __future__ import annotations

import asyncio
import json
import sys
from argparse import ArgumentParser

from . import autodiscover
from .registry import autodiscover_prompts
from .registry import get_agent
from .runner import run_agent_with_events
from .memory import BackendMemory, InMemoryMemory
from .llm import OpenAILLM


def _parser() -> ArgumentParser:
    p = ArgumentParser(prog="agents-cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="Проверить, что автодискавери проходит (импортирует under_hood)")

    runp = sub.add_parser("run", help="Запустить агента и вывести события в stdout")
    runp.add_argument("id")
    runp.add_argument("version")
    runp.add_argument("--session", required=True)
    runp.add_argument("--query", default="")
    runp.add_argument("--memory", choices=["backend", "inmem"], default="backend", help="Источник памяти: backend или in-memory")

    return p


async def _cmd_list(args):  # pragma: no cover - простой вывод
    autodiscover_prompts()
    autodiscover()
    print("OK: under_hood imported and decorators executed.")


async def _cmd_run(args):
    autodiscover_prompts()
    autodiscover()
    memory = BackendMemory() if args.memory == "backend" else InMemoryMemory()
    # AICODE-NOTE: Инициализируем LLM и передаём в фабрику агента. Клиент создаётся внутри реализации.
    llm = OpenAILLM()
    agent = get_agent(args.id, args.version, memory=memory, llm=llm)
    async for ev in run_agent_with_events(agent, session_id=args.session, user_message=args.query):
        print(json.dumps(ev.model_dump(), ensure_ascii=False))


def main(argv=None):  # pragma: no cover - точка входа
    argv = argv or sys.argv[1:]
    parser = _parser()
    args = parser.parse_args(argv)
    if args.cmd == "list":
        asyncio.run(_cmd_list(args))
    elif args.cmd == "run":
        asyncio.run(_cmd_run(args))


if __name__ == "__main__":  # pragma: no cover
    main()


# python -m agents.cli run learning_planner v1 --session dev-s1 --query "Python" --memory inmem