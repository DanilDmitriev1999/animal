from openai import OpenAI
import json
import os
import dotenv

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


dotenv.load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

# AICODE-NOTE: При strict=True сервис требует перечислить ВСЕ ключи из properties в required, иначе 400
schema = {
    "name": "todo_item",
    "strict": True,            # просим строгое соблюдение схемы
    "schema": {
        "type": "object",
        "properties": {
            "title":   {"type": "string"},
            "due_iso": {"type": "string"},
            "priority":{"type": "string", "enum": ["low","med","high"]}
        },
        "required": ["title", "due_iso", "priority"],
        "additionalProperties": False
    }
}

class TodoItem(BaseModel):
    # AICODE-NOTE: extra="forbid" -> "additionalProperties": false в JSON Schema
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    due_iso: str = Field(description="ISO дата, например 2025-08-11")
    priority: Literal["low", "med", "high"]

resp = client.beta.chat.completions.parse(
    model="gpt-4.1-mini",
    messages=[{"role":"user","content":"Сформируй задачу: купить кофе завтра, высокий приоритет"}],
    # response_format={"type":"json_schema","json_schema": schema}
    response_format=TodoItem
)

data = resp.choices[0].message.content
print(data)  # {'title': 'Купить кофе', 'due_iso': '2025-08-11', 'priority': 'high'}
print(type(data))
print(resp.choices[0].message.parsed)
