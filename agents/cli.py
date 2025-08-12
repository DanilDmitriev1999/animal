"""
// AICODE-NOTE: Простой CLI для регистрации и запуска агентов (симуляция бэкенда).

Примеры:
  python -m agents.cli list
  python -m agents.cli run learning_planner v1 --session s1 --query "Python"
  # Специальный режим планировщика курса (готовые параметры формы)
  python -m agents.cli run_learning_planner --session dev-s1 \
    --title "Введение в нейросети" \
    --description "Чтобы агент понял контекст" \
    --goal "Написать первую нейросеть" \
    --focus theory \
    --tone friendly \
    --memory inmem

  # Специальный режим менеджера конспекта (создание/обновление)
  python -m agents.cli run_synopsis_manager --session dev-s1 \
    --action create \
    --title "Введение в нейросети" \
    --description "Краткое описание" \
    --goal "Понять базовые понятия" \
    --focus theory \
    --tone friendly \
    --plan "Введение" --plan "Ключевые понятия" --plan "Практика"
"""

from __future__ import annotations

import asyncio
import json
import sys
from argparse import ArgumentParser
from typing import Any, Dict

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

    runp = sub.add_parser("run", help="Запустить произвольного агента и вывести события в stdout")
    runp.add_argument("id")
    runp.add_argument("version")
    runp.add_argument("--session", required=True)
    runp.add_argument("--query", default="", help="Свободный текст (старый контракт user_message)")
    runp.add_argument("--memory", choices=["backend", "inmem"], default="backend", help="Источник памяти: backend или in-memory")

    # Специальный режим для learning_planner (готовые параметры формы)
    runlp = sub.add_parser("run_learning_planner", help="Запустить learning_planner с параметрами формы")
    runlp.add_argument("--session", required=True)
    runlp.add_argument("--title", required=False, default="Введение в нейросети")
    runlp.add_argument("--description", required=False, default="Чтобы агент понял контекст")
    runlp.add_argument("--goal", required=False, default="Написать первую нейросеть")
    runlp.add_argument("--focus", choices=["theory", "practice"], default="theory")
    runlp.add_argument("--tone", choices=["strict", "friendly", "motivational", "neutral"], default="friendly")
    runlp.add_argument("--memory", choices=["backend", "inmem"], default="inmem")

    # Специальный режим для synopsis_manager (создание/обновление конспекта)
    runsyn = sub.add_parser("run_synopsis_manager", help="Запустить synopsis_manager для создания/обновления конспекта")
    runsyn.add_argument("--session", required=True)
    runsyn.add_argument("--action", choices=["create", "update"], default="create")
    runsyn.add_argument("--title", required=False, default="Название курса")
    runsyn.add_argument("--description", required=False, default="Краткое описание курса")
    runsyn.add_argument("--goal", required=False, default="Цель обучения")
    runsyn.add_argument("--focus", choices=["theory", "practice"], default="theory")
    runsyn.add_argument("--tone", choices=["strict", "friendly", "motivational", "neutral"], default="friendly")
    runsyn.add_argument("--plan", action="append", default=[], help="Пункт плана; можно передать несколько флагов --plan")
    runsyn.add_argument("--instructions", required=False, default=None, help="Свободные правки/уточнения для обновления")
    runsyn.add_argument("--memory", choices=["backend", "inmem"], default="inmem")

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


async def _cmd_run_learning_planner(args):
    autodiscover_prompts()
    autodiscover()

    memory = BackendMemory() if args.memory == "backend" else InMemoryMemory()

    query: Dict[str, Any] = {
        "title": args.title,
        "description": args.description,
        "goal": args.goal,
        "focus": args.focus,
        "tone": args.tone,
    }

    llm = OpenAILLM()
    agent = get_agent("learning_planner", "v1", memory=memory, llm=llm)

    async for ev in run_agent_with_events(agent, session_id=args.session, query=query):
        print(json.dumps(ev.model_dump(), ensure_ascii=False))


async def _cmd_run_synopsis_manager(args):
    autodiscover_prompts()
    autodiscover()

    memory = BackendMemory() if args.memory == "backend" else InMemoryMemory()

    query: Dict[str, Any] = {
        "action": args.action,
        "params": {
            "title": args.title,
            "description": args.description,
            "goal": args.goal,
            "focus": args.focus,
            "tone": args.tone,
        },
        "plan": list(args.plan or []),
    }
    if args.instructions:
        query["instructions"] = args.instructions

    llm = OpenAILLM()
    agent = get_agent("synopsis_manager", "v1", memory=memory, llm=llm)

    async for ev in run_agent_with_events(agent, session_id=args.session, query=query):
        print(json.dumps(ev.model_dump(), ensure_ascii=False))


def main(argv=None):  # pragma: no cover - точка входа
    argv = argv or sys.argv[1:]
    parser = _parser()
    args = parser.parse_args(argv)
    if args.cmd == "list":
        asyncio.run(_cmd_list(args))
    elif args.cmd == "run":
        asyncio.run(_cmd_run(args))
    elif args.cmd == "run_learning_planner":
        asyncio.run(_cmd_run_learning_planner(args))
    elif args.cmd == "run_synopsis_manager":
        asyncio.run(_cmd_run_synopsis_manager(args))


if __name__ == "__main__":  # pragma: no cover
    main()


# python -m agents.cli run learning_planner v1 --session dev-s1 --query "Python" --memory inmem
# python -m agents.cli run_learning_planner --session dev-s1 --title "Введение в нейросети" --description "Чтобы агент понял контекст" --goal "Написать первую нейросеть" --focus theory --tone friendly --memory inmem

# создание
# python -m agents.cli run_synopsis_manager --session dev-s1 \
# --action create \
# --title "Введение в нейросети" \
# --description "Краткое описание" \
# --goal "Понять базовые понятия" \
# --focus theory \
# --tone friendly \
# --plan "Введение" --plan "Ключевые понятия" --plan "Практика" \
# --memory inmem

# # обновление (с правками)
# python -m agents.cli run_synopsis_manager --session dev-s1 \
# --action update \
# --title "Введение в нейросети" \
# --description "Краткое описание" \
# --goal "Понять базовые понятия" \
# --focus practice \
# --tone neutral \
# --plan "Обновлённый модуль 1" --plan "Новый модуль 2" \
# --instructions "Добавь определения для overfitting/underfitting и список шагов внедрения." \
# --memory inmem

# python3 -m agents.cli run mentor_chat v1 --session dev-s1 --query "Как лучше начать этот курс?" --memory inmem

# python3 -m agents.cli run practice_coach v1 --session dev-s1 --query "Хочу первую задачу по теме" --memory inmem

# python3 -m agents.cli run simulation_mentor v1 --session dev-s1 --query "Смоделируй разговор с заказчиком" --memory inmem