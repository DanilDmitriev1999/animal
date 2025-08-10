import * as React from "react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { GlassCard } from "./GlassCard"
import { ChevronUp, ListChecks, StickyNote } from "lucide-react"
import { cn } from "@/lib/utils"

export type SynopsisItem =
  | { type: "heading"; text: string }
  | { type: "text"; text: string }
  | { type: "definition"; term: string; description: string }
  | { type: "code"; language?: string; code: string }
  | { type: "note"; text: string }
  | { type: "list"; items: string[] }

export interface LiveSynopsisProps {
  items: SynopsisItem[]
  lastUpdated: string
  className?: string
  // AICODE-NOTE: Позволяет управлять стартовым состоянием разворота
  defaultOpen?: boolean
}

const CodeBlock = ({ language, code }: { language?: string; code: string }) => (
  <pre className="mt-2 overflow-x-auto rounded-md bg-black/80 p-3 text-xs leading-relaxed text-white">
    <code>
      {language ? `// ${language}\n` : null}
      {code}
    </code>
  </pre>
)

const LiveSynopsis = React.forwardRef<HTMLDivElement, LiveSynopsisProps>(
  ({ items, lastUpdated, className, defaultOpen }, ref) => {
    // AICODE-NOTE: Collapsed by default to reduce visual competition with chat
    const [isOpen, setIsOpen] = React.useState(!!defaultOpen)

    return (
      <GlassCard ref={ref} variant="neumorph" className={cn("p-6", className)}>
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ListChecks className="h-5 w-5 text-text-secondary" />
              <h3 className="font-semibold text-text-primary">Live Synopsis</h3>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-text-secondary">{lastUpdated}</span>
              <CollapsibleTrigger asChild>
                <button aria-label="Toggle synopsis">
                  <ChevronUp
                    className={cn(
                      "h-5 w-5 text-text-secondary transition-transform",
                      isOpen ? "rotate-0" : "rotate-180"
                    )}
                  />
                </button>
              </CollapsibleTrigger>
            </div>
          </div>

          <CollapsibleContent>
            <div className="mt-4 space-y-4 text-sm text-text-secondary">
              {items.map((item, idx) => {
                switch (item.type) {
                  case "heading":
                    return (
                      <h4 key={idx} className="text-base font-semibold text-text-primary">
                        {item.text}
                      </h4>
                    )
                  case "text":
                    return (
                      <p key={idx} className="leading-relaxed">
                        {item.text}
                      </p>
                    )
                  case "definition":
                    return (
                      <div key={idx} className="rounded-md border border-white/10 p-3">
                        <div className="text-text-primary font-medium">{item.term}</div>
                        <div className="mt-1 text-sm text-text-secondary">{item.description}</div>
                      </div>
                    )
                  case "code":
                    return <CodeBlock key={idx} language={item.language} code={item.code} />
                  case "note":
                    return (
                      <div key={idx} className="flex items-start gap-2 rounded-md bg-white/5 p-3">
                        <StickyNote className="mt-0.5 h-4 w-4 text-text-secondary" />
                        <p className="leading-relaxed">{item.text}</p>
                      </div>
                    )
                  case "list":
                    return (
                      <ul key={idx} className="list-disc space-y-1 pl-6">
                        {item.items.map((li, i) => (
                          <li key={i}>{li}</li>
                        ))}
                      </ul>
                    )
                  default:
                    return null
                }
              })}
            </div>
          </CollapsibleContent>
        </Collapsible>
      </GlassCard>
    )
  }
)

LiveSynopsis.displayName = "LiveSynopsis"

export { LiveSynopsis }