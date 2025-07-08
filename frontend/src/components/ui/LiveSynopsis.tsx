import * as React from "react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { GlassCard } from "./GlassCard"
import { ChevronUp, ListChecks } from "lucide-react"
import { cn } from "@/lib/utils"

export interface LiveSynopsisProps {
  points: string[]
  lastUpdated: string
  className?: string
}

const LiveSynopsis = React.forwardRef<HTMLDivElement, LiveSynopsisProps>(
  ({ points, lastUpdated, className }, ref) => {
    const [isOpen, setIsOpen] = React.useState(true)

    return (
      <GlassCard ref={ref} className={cn("p-6", className)}>
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
            <ul className="mt-4 list-disc space-y-2 pl-8 text-sm text-text-secondary">
              {points.map((point, index) => (
                <li key={index}>{point}</li>
              ))}
            </ul>
          </CollapsibleContent>
        </Collapsible>
      </GlassCard>
    )
  }
)

LiveSynopsis.displayName = "LiveSynopsis"

export { LiveSynopsis } 