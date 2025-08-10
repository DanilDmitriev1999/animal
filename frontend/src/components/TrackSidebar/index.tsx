"use client"

import * as React from "react"
import { GlassCard } from "@/components/ui/GlassCard"
import { cn } from "@/lib/utils"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { ChevronUp, CheckCircle2, Circle, Info } from "lucide-react"

export interface TrackSidebarProps extends React.HTMLAttributes<HTMLDivElement> {
  description: string
  goal: string
  status: string
  roadmap?: { title: string; done?: boolean }[]
}

export const TrackSidebar = React.forwardRef<HTMLDivElement, TrackSidebarProps>(
  ({ className, description, goal, status, roadmap = [], ...props }, ref) => {
    const splitToParagraphs = (text: string): string[] => {
      const byNewlines = text.split(/\n{2,}/).map((t) => t.trim()).filter(Boolean)
      if (byNewlines.length > 1) return byNewlines
      const sentences = text.split(/(?<=[.!?])\s+/).filter(Boolean)
      const grouped: string[] = []
      for (let i = 0; i < sentences.length; i += 2) {
        grouped.push([sentences[i], sentences[i + 1]].filter(Boolean).join(" "))
      }
      return grouped.length ? grouped : [text]
    }

    const [infoOpen, setInfoOpen] = React.useState(true)
    const [statusOpen, setStatusOpen] = React.useState(true)
    const [roadmapOpen, setRoadmapOpen] = React.useState(true)

    const renderParagraph = (p: string, key: React.Key) => {
      // Простое выделение меток вида "Рекомендация:" жирным
      const hasLabel = p.includes(":") && p.split(":")[0].length <= 16
      if (!hasLabel) return <p key={key}>{p}</p>
      const [label, rest] = [p.split(":")[0], p.slice(p.indexOf(":") + 1).trim()]
      return (
        <p key={key}>
          <span className="font-semibold text-text-primary">{label}:</span>{" "}
          <span>{rest}</span>
        </p>
      )
    }

    return (
      <div ref={ref} className={cn("space-y-4", className)} {...props}>
        {/* AICODE-NOTE: Объединённый блок информации о треке (Описание + Цель) с возможностью сворачивания */}
        <GlassCard variant="neumorph" className="p-6">
          <Collapsible open={infoOpen} onOpenChange={setInfoOpen}>
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-text-primary">Информация о треке</h4>
              <CollapsibleTrigger asChild>
                <button aria-label="Toggle track info">
                  <ChevronUp className={cn("h-5 w-5 text-text-secondary transition-transform", infoOpen ? "rotate-0" : "rotate-180")} />
                </button>
              </CollapsibleTrigger>
            </div>
            <CollapsibleContent>
              <div className="mt-3 space-y-4">
                <div>
                  <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-text-primary">Описание</div>
                  <div className="space-y-2 text-sm leading-relaxed text-text-secondary">
                    {splitToParagraphs(description).map((p, i) => (
                      <p key={i}>{p}</p>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-text-primary">Цель</div>
                  <div className="space-y-2 text-sm leading-relaxed text-text-secondary">
                    {splitToParagraphs(goal).map((p, i) => (
                      <p key={i}>{p}</p>
                    ))}
                  </div>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </GlassCard>

        {/* AICODE-NOTE: Статус от AI агента с возможностью сворачивания */}
        <GlassCard variant="neumorph" className="p-6">
          <Collapsible open={statusOpen} onOpenChange={setStatusOpen}>
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-text-primary">Статус от AI агента</h4>
              <CollapsibleTrigger asChild>
                <button aria-label="Toggle AI status">
                  <ChevronUp className={cn("h-5 w-5 text-text-secondary transition-transform", statusOpen ? "rotate-0" : "rotate-180")} />
                </button>
              </CollapsibleTrigger>
            </div>
            <CollapsibleContent>
              <div className="mt-2 space-y-2 text-sm leading-relaxed text-text-secondary">
                {splitToParagraphs(status).map((p, i) => renderParagraph(p, i))}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </GlassCard>

        {/* AICODE-NOTE: Roadmap обучения — может меняться; выполненные шаги перечёркнуты */}
        {roadmap && roadmap.length > 0 ? (
          <GlassCard variant="neumorph" className="p-6">
            <Collapsible open={roadmapOpen} onOpenChange={setRoadmapOpen}>
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-text-primary">Roadmap</h4>
                <CollapsibleTrigger asChild>
                  <button aria-label="Toggle roadmap">
                    <ChevronUp className={cn("h-5 w-5 text-text-secondary transition-transform", roadmapOpen ? "rotate-0" : "rotate-180")} />
                  </button>
                </CollapsibleTrigger>
              </div>
              <CollapsibleContent>
                <ul className="mt-3 space-y-2">
                  {roadmap.map((step, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-text-secondary">
                      {step.done ? (
                        <CheckCircle2 className="mt-0.5 h-4 w-4 opacity-70" />
                      ) : (
                        <Circle className="mt-0.5 h-4 w-4 opacity-70" />
                      )}
                      <span className={cn(step.done && "line-through opacity-60")}>{step.title}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-3 flex items-start gap-2 rounded-md border border-white/10 bg-white/5 p-2 text-xs text-text-secondary">
                  <Info className="mt-0.5 h-3.5 w-3.5" />
                  <span>
                    Примечание: дорожная карта обновляется автоматически по рекомендациям AI‑агента и может меняться.
                  </span>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </GlassCard>
        ) : null}

      </div>
    )
  }
)

TrackSidebar.displayName = "TrackSidebar"

export default TrackSidebar


