# AI Learning UI

## Как подключать нового агента на фронтенде

- **Клиент API**: все обращения к бэкенду идут через `src/lib/api.ts`.
- **Рекомендация**: для каждого нового агента добавляйте один метод в `api` с понятной сигнатурой, без прямых `fetch` из компонентов.

### Пример: агент планировщика `learning_planner`

1) Добавьте метод в `src/lib/api.ts`:
```ts
runLearningPlanner(params: {
  sessionId?: string
  query: {
    title: string
    description: string
    goal: string
    focus: 'theory' | 'practice'
    tone: 'strict' | 'friendly' | 'motivational' | 'neutral'
  }
  memory?: 'backend' | 'inmem'
}): Promise<{ plan: { modules: string[] }; sources: unknown[] }>
```

2) Используйте метод в странице/компоненте:
```ts
const res = await api.runLearningPlanner({ query: { title, description, goal, focus, tone }, memory: 'inmem' })
setRoadmap(res.plan.modules.map((text, i) => ({ id: `${Date.now()}_${i}`, text })))
```

3) UX‑паттерн для асинхронных агентов:
- мгновенно переключайтесь на целевую секцию (например, шаг 2 мастера);
- показывайте спиннер/скелетоны «Агент формирует план…»;
- по завершении подменяйте плейсхолдеры реальными данными;
- блокируйте действие «Сохранить/Создать» на время генерации.

### Окружение
Создайте `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIXED_DEVICE_ID=dev-device
```

### Где смотреть существующую интеграцию
- Метод клиента: `src/lib/api.ts` → `runLearningPlanner`
- UI мастера создания трека: `src/app/tracks/create/page.tsx`

### Пример: агент конспекта `synopsis_manager`

1) Добавьте метод в `src/lib/api.ts` (уже добавлен: `runSynopsisManager`). Сигнатура:
```ts
runSynopsisManager(params: {
  sessionId?: string
  query: {
    action: 'create' | 'update'
    params: {
      title: string
      description: string
      goal: string
      focus: 'theory' | 'practice'
      tone: 'strict' | 'friendly' | 'motivational' | 'neutral'
    }
    plan?: string[]
    synopsis?: unknown[]
    instructions?: string | null
  }
  memory?: 'backend' | 'inmem'
}): Promise<{ synopsis: { items: any[]; lastUpdated?: string | null }; sources: unknown[] }>
```

2) Пример использования (после подтверждения роадмапа):
```ts
const res = await api.runSynopsisManager({
  query: {
    action: 'create',
    params: { title, description, goal, focus, tone },
    plan: roadmap.map(r => r.text)
  },
  memory: 'inmem'
})
// res.synopsis.items — данные для LiveSynopsis
```
