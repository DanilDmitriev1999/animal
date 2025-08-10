'use client'

import * as React from "react"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Header } from "@/components/layout/Header"
import { LiveSynopsis, type SynopsisItem } from "@/components/ui/LiveSynopsis"
import { ContentTabs } from "@/components/ui/ContentTabs"
import { ChatMessage } from "@/components/ui/ChatMessage"
import { Button } from "@/components/ui/button"
import { ListChecks, X } from "lucide-react"
import ChatComposer from "@/components/ChatComposer"
import TrackSidebar from "@/components/TrackSidebar"
import { api, type Message as ApiMessage, type Track } from "@/lib/api"
import { getDeviceId } from "@/lib/device"

// AICODE-NOTE: Моки удалены. Дальше данные будут приходить из API.

const TrackPage = ({ params }: { params: Promise<{ slug: string }> }) => {
  const { slug } = React.use(params)
  const chatContainerRef = React.useRef<HTMLDivElement>(null)
  // AICODE-NOTE: Control active tab to tie composer and mobile synopsis
  const [activeTab, setActiveTab] = React.useState<string>("chat")
  // AICODE-NOTE: Toggle for desktop synopsis side panel
  const [isSynopsisPanelVisible, setSynopsisPanelVisible] = React.useState<boolean>(true)
  // AICODE-NOTE: Track viewport for desktop/mobile branching
  const [isLgUp, setIsLgUp] = React.useState<boolean>(false)
  // AICODE-NOTE: Local state for three independent threads and evolving synopsis
  type Message = { role: "user" | "assistant"; message: string; avatarUrl?: string }
  const [messages, setMessages] = React.useState<{ chat: Message[]; practice: Message[]; simulation: Message[] }>({
    chat: [],
    practice: [],
    simulation: [],
  })
  const [synopsisItems, setSynopsisItems] = React.useState<SynopsisItem[]>([])
  const [lastUpdatedAt, setLastUpdatedAt] = React.useState<Date>(new Date())
  const [composerValue, setComposerValue] = React.useState<string>("")
  const containerRef = React.useRef<HTMLDivElement>(null)
  // AICODE-NOTE: Контролируем оверлей конспекта
  const [isSynopsisOverlayOpen, setSynopsisOverlayOpen] = React.useState<boolean>(false)
  const [track, setTrack] = React.useState<Track | null>(null)
  const [sessionId, setSessionId] = React.useState<string | null>(null)
  const [roadmap, setRoadmap] = React.useState<{ title: string; done?: boolean }[]>([])
  const [loading, setLoading] = React.useState<boolean>(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [activeTab, messages])

  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(min-width: 1024px)')
    const update = () => setIsLgUp(mediaQuery.matches)
    update()
    mediaQuery.addEventListener('change', update)
    return () => mediaQuery.removeEventListener('change', update)
  }, [])

  // AICODE-NOTE: Первичная загрузка данных трека + создание/получение сессии + загрузка сообщений
  React.useEffect(() => {
    let mounted = true
    const deviceId = getDeviceId()
    ;(async () => {
      try {
        const [t, sid] = await Promise.all([
          api.getTrack(slug),
          api.createOrGetSession(deviceId, slug),
        ])
        if (!mounted) return
        setTrack(t)
        setSessionId(sid)
        const [rmap, chat, practice, simulation] = await Promise.all([
          api.getRoadmap(slug),
          api.getMessages(sid, 'chat'),
          api.getMessages(sid, 'practice'),
          api.getMessages(sid, 'simulation'),
        ])
        setRoadmap(rmap.map(r => ({ title: r.text, done: r.done })))
        const map = (arr: ApiMessage[]): Message[] => arr.map(m => ({ role: m.role as any, message: m.content }))
        setMessages({ chat: map(chat), practice: map(practice), simulation: map(simulation) })
      } catch (e) {
        if (mounted) setError(String(e))
      } finally {
        if (mounted) setLoading(false)
      }
    })()
    return () => {
      mounted = false
    }
  }, [slug])

  const handleSynopsisButton = () => {
    setSynopsisPanelVisible((v) => !v)
    // AICODE-NOTE: При открытии/закрытии боковой панели фокус ввода направляем в чат
    setActiveTab('chat')
  }

  const handleSend = () => {
    const trimmed = composerValue.trim()
    if (!trimmed) return
    if (!sessionId) return
    const target = activeTab as 'chat' | 'practice' | 'simulation'
    // AICODE-NOTE: Append user message to the active chat thread
    const userMsg: Message = { role: 'user', message: trimmed, avatarUrl: 'https://github.com/shadcn.png' }
    setMessages(prev => ({
      ...prev,
      [target]: [...prev[target], userMsg],
    }))
    // AICODE-NOTE: Отправляем на сервер (ошибку не блокируем UI, но можно улучшить)
    api.postMessage(sessionId, target, { role: 'user', content: trimmed }).catch(() => {})
    // AICODE-NOTE: Naive synopsis enrichment: append user's message as a note item
    setSynopsisItems(prev => [
      ...prev,
      { type: 'note', text: trimmed.length > 160 ? trimmed.slice(0, 160) + '…' : trimmed },
    ])
    setLastUpdatedAt(new Date())
    setComposerValue("")
  }

  const renderThread = (items: Message[]) => (
    <div ref={chatContainerRef} className="space-y-6 pr-4 max-h-[60vh] overflow-y-auto">
      {/* AICODE-NOTE: Фиксированный вступительный месседж от AI-агента */}
      <ChatMessage
        role="assistant"
        message="Я ваш AI‑ментор. Спрашивайте про курс, практику или запустите симуляцию — помогу шаг за шагом."
      />
      {items.map((msg, index) => (
        <ChatMessage
          key={index}
          role={msg.role as "user" | "assistant"}
          message={msg.message}
          avatarUrl={(msg as any).avatarUrl}
        />
      ))}
    </div>
  )

  const renderWithComposer = (items: Message[], ph: string) => (
    <div className="mx-auto max-w-3xl">
      {renderThread(items)}
      <div className="mt-4">
        <ChatComposer
          value={composerValue}
          onChange={setComposerValue}
          onSend={handleSend}
          placeholder={ph}
          quickCommands={[]}
        />
      </div>
    </div>
  )
  const chatContent = renderWithComposer(messages.chat, "Спросите что-нибудь о курсе…")
  const practiceChatContent = renderWithComposer(messages.practice, "Спросите что-нибудь по практике…")
  const simulationChatContent = renderWithComposer(messages.simulation, "Спросите что-нибудь для симуляции…")

  return (
    <div className="flex flex-col h-screen bg-background">
      <Header isAuthenticated={true} />
      {/* AICODE-NOTE: Глобально закреплённые контроли под хедером. Не влияют на скролл контента. */}
      <div className="pointer-events-none fixed right-6 top-20 z-40 flex gap-2">
        <div className="pointer-events-auto">
          <Button variant="outline" size="sm" onClick={() => { setSynopsisOverlayOpen(true); setActiveTab('chat') }} aria-label="Open synopsis overlay">
            <ListChecks className="h-4 w-4 mr-2" />
            Конспект
          </Button>
        </div>
        <div className="pointer-events-auto hidden lg:inline-flex">
          <Button variant="outline" size="sm" onClick={handleSynopsisButton} aria-label="Toggle sidebar">
            {isSynopsisPanelVisible ? 'Скрыть панель' : 'Показать панель'}
          </Button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto pb-8">
        <main className="container mx-auto px-4 py-8" ref={containerRef}>
            <Breadcrumb className="mb-6">
                <BreadcrumbList>
                    <BreadcrumbItem>
                        <BreadcrumbLink href="/tracks">Tracks</BreadcrumbLink>
                    </BreadcrumbItem>
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                    <BreadcrumbPage>{track?.title ?? slug}</BreadcrumbPage>
                    </BreadcrumbItem>
                </BreadcrumbList>
            </Breadcrumb>
            
            {/* AICODE-NOTE: Two-column responsive layout. On desktop, right sticky panel shows synopsis. On mobile, synopsis is available as a tab. */}
            

              <div className={isSynopsisPanelVisible ? "lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(320px,420px)] lg:gap-6" : "lg:block"}>
              <div>
                <ContentTabs 
                  chatContent={chatContent}
                  practiceContent={practiceChatContent}
                  simulationContent={simulationChatContent}
                  value={activeTab}
                  onValueChange={setActiveTab}
                />
              </div>
              {isSynopsisPanelVisible && (
                <aside className="hidden lg:block">
                  <div
                    className="sticky top-20 overflow-y-auto pr-2"
                    style={{ height: "calc(100vh - 120px)" }}
                  >
                    <TrackSidebar
                      description={track?.description ?? ''}
                      goal={track?.goal ?? ''}
                      status={''}
                        roadmap={roadmap}
                    />
                  </div>
                </aside>
              )}
            </div>
            {/* AICODE-NOTE: Overlay for Live Synopsis */}
            {isSynopsisOverlayOpen && (
              <div
                className="fixed inset-0 z-50 bg-black/40 backdrop-blur-[2px]"
                onClick={() => setSynopsisOverlayOpen(false)}
                aria-modal="true"
                role="dialog"
              >
                <div
                  className="fixed right-6 top-24 w-[min(92vw,520px)]"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    aria-label="Close synopsis overlay"
                    onClick={() => setSynopsisOverlayOpen(false)}
                    className="absolute -right-2 -top-2 z-50 inline-flex h-8 w-8 items-center justify-center rounded-full bg-white/90 text-black shadow hover:bg-white"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <LiveSynopsis
                    items={synopsisItems}
                    lastUpdated={lastUpdatedAt.toLocaleTimeString()}
                    defaultOpen
                  />
                </div>
              </div>
            )}
        </main>
      </div>
    </div>
  )
}

export default TrackPage 