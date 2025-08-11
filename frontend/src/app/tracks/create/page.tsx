'use client'

import * as React from 'react'
import { Header } from '@/components/layout/Header'
import { GlassCard } from '@/components/ui/GlassCard'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { useSearchParams } from 'next/navigation'
import { api } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'

type LearningFocus = 'theory' | 'practice'
type Tone = 'strict' | 'friendly' | 'motivational' | 'neutral'

type RoadmapItem = { id: string; text: string }

export default function CreateTrackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [step, setStep] = React.useState<1 | 2>(1)
  const [title, setTitle] = React.useState('')
  const [description, setDescription] = React.useState('')
  const [goal, setGoal] = React.useState('')
  const [focus, setFocus] = React.useState<LearningFocus>('theory')
  const [tone, setTone] = React.useState<Tone>('friendly')
  const [roadmap, setRoadmap] = React.useState<RoadmapItem[]>([])
  const [loadingPlan, setLoadingPlan] = React.useState<boolean>(false)

  const canNext = title.trim().length > 1 && description.trim().length > 10 && goal.trim().length > 3

  const generateDraftRoadmap = React.useCallback((): RoadmapItem[] => {
    const base: string[] = [
      'Вступление и постановка задачи',
      'Ключевые понятия и термины',
      focus === 'theory' ? 'Глубокая теория с примерами' : 'Практикум: первая мини‑задача',
      'Типичные ошибки и как их избегать',
      focus === 'practice' ? 'Проект: применяем знания' : 'Обзор дополнительных материалов',
      'Итоги и дальнейшие шаги',
    ]
    return base.map((t, i) => ({ id: `${Date.now()}_${i}`, text: t }))
  }, [focus])

  const handleNext = async () => {
    if (!canNext) return
    setStep(2)
    setLoadingPlan(true)
    const query = { title, description, goal, focus, tone }
    try {
      const res = await api.runLearningPlanner({ query, memory: 'inmem' })
      const modules = res.plan.modules ?? []
      setRoadmap(modules.map((text: string, i: number) => ({ id: `${Date.now()}_${i}`, text })))
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error('Не удалось сгенерировать план', e)
      const base = [
        'Вступление и постановка задачи',
        'Ключевые понятия и термины',
        focus === 'theory' ? 'Глубокая теория с примерами' : 'Практикум: первая мини‑задача',
        'Типичные ошибки и как их избегать',
        focus === 'practice' ? 'Проект: применяем знания' : 'Обзор дополнительных материалов',
      ]
      setRoadmap(base.map((t, i) => ({ id: `${Date.now()}_${i}`, text: t })))
    } finally {
      setLoadingPlan(false)
    }
  }

  const handleAddItem = () => {
    setRoadmap(prev => [...prev, { id: `${Date.now()}`, text: '' }])
  }
  const handleChangeItem = (id: string, text: string) => {
    setRoadmap(prev => prev.map(it => (it.id === id ? { ...it, text } : it)))
  }
  const handleRemoveItem = (id: string) => {
    setRoadmap(prev => prev.filter(it => it.id !== id))
  }

  const handleSubmit = async () => {
    if (!title.trim()) return
    const plan = roadmap.map(r => r.text).filter(Boolean)
    try {
      const track = await api.createTrack({ title, description, goal, roadmap: plan })
      const slug = encodeURIComponent(track.slug)
      // Переходим на созданный трек
      router.push(`/tracks/${slug}`)
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error('Не удалось создать трек', e)
      alert('Не удалось создать трек')
    }
  }

  // AICODE-NOTE: Мок-режим удалён.

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header isAuthenticated={true} />
      <main className="container mx-auto flex-1 px-4 py-8">
        {searchParams.get('mock') === '1' && (
          <div className="mx-auto mb-4 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2 text-sm text-text-secondary">
              <span>Мок-режим:</span>
              <Button size="sm" variant="outline" onClick={() => setStep(1)}>Шаг 1</Button>
              <Button size="sm" variant="outline" onClick={() => { setRoadmap(generateDraftRoadmap()); setStep(2) }}>Шаг 2</Button>
            </div>
          </div>
        )}
        {step === 1 ? (
          <GlassCard className="mx-auto max-w-3xl p-6">
            <h1 className="mb-4 text-2xl font-bold">Создание трека — шаг 1/2</h1>
            <div className="space-y-5">
              <div>
                <label className="mb-1 block text-sm text-text-secondary">Название трека</label>
                <Input
                  placeholder="Например: Введение в нейронные сети"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-text-secondary">Описание</label>
                <Textarea
                  placeholder="Чтобы агент понял контекст и сформировал вводный блок"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-text-secondary">Ключевая цель обучения</label>
                <Input
                  placeholder="Например: Написать первую нейросеть"
                  value={goal}
                  onChange={e => setGoal(e.target.value)}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm text-text-secondary">Тип обучения</label>
                  <select
                    className="dark:bg-input/30 border-input h-9 w-full rounded-input border bg-transparent px-3 text-sm outline-none focus:border-ring focus:ring-ring/50 focus:ring-[3px]"
                    value={focus}
                    onChange={e => setFocus(e.target.value as LearningFocus)}
                  >
                    <option value="theory">Акцент на теорию</option>
                    <option value="practice">Акцент на практику</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm text-text-secondary">Тон обучения</label>
                  <select
                    className="dark:bg-input/30 border-input h-9 w-full rounded-input border bg-transparent px-3 text-sm outline-none focus:border-ring focus:ring-ring/50 focus:ring-[3px]"
                    value={tone}
                    onChange={e => setTone(e.target.value as Tone)}
                  >
                    <option value="friendly">Дружелюбный</option>
                    <option value="motivational">Подбадривающий</option>
                    <option value="strict">Строгий</option>
                    <option value="neutral">Нейтральный</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button variant="outline" onClick={() => history.back()}>Отмена</Button>
                <Button disabled={!canNext} onClick={handleNext}>Далее</Button>
              </div>
            </div>
          </GlassCard>
        ) : (
          <GlassCard className="mx-auto max-w-3xl p-6">
            <h1 className="mb-1 text-2xl font-bold">Черновой роадмап — шаг 2/2</h1>
            <div className="mb-4 flex items-center gap-2 text-sm text-text-secondary">
              {loadingPlan ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Агент формирует план курса…</span>
                </>
              ) : (
                <p>Агент предложил план. Отредактируйте пункты, удалите или добавьте свои.</p>
              )}
            </div>
            <div className="space-y-3">
              {loadingPlan && roadmap.length === 0 ? (
                <div className="space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="h-10 rounded-input bg-input/30 animate-pulse" />
                  ))}
                </div>
              ) : (
              roadmap.map((item, idx) => (
                <div key={item.id} className="flex items-center gap-3">
                  <span className="w-6 select-none text-right text-sm text-text-secondary">{idx + 1}</span>
                  <Input
                    value={item.text}
                    placeholder="Текст пункта"
                    onChange={e => handleChangeItem(item.id, e.target.value)}
                  />
                  <Button variant="ghost" onClick={() => handleRemoveItem(item.id)} aria-label="Удалить">✕</Button>
                </div>
              ))
              )}
              <div>
                <Button variant="outline" onClick={handleAddItem} disabled={loadingPlan}>Добавить пункт</Button>
              </div>
            </div>
            <div className="mt-6 flex justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>Назад</Button>
              <Button onClick={handleSubmit} disabled={loadingPlan}>Создать трек</Button>
            </div>
          </GlassCard>
        )}
      </main>
    </div>
  )
}


