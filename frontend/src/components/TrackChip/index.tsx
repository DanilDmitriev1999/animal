"use client"

import * as React from "react"
import { GlassCard } from "@/components/ui/GlassCard"
import { cn } from "@/lib/utils"

export interface TrackChipProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string
  active?: boolean
  status?: "none" | "in-progress" | "done"
}

// AICODE-NOTE: Compact track selector chip to replace large cards on the /tracks page
export const TrackChip = React.forwardRef<HTMLDivElement, TrackChipProps>(
  ({ className, title, active = false, status = "none", ...props }, ref) => {
    const statusColor =
      status === "done" ? "bg-emerald-500" : status === "in-progress" ? "bg-primary" : "bg-white/30"

    return (
      <GlassCard
        ref={ref}
        asChild
        shape="pill"
        variant="neumorph"
        className={cn(
          // AICODE-NOTE: Remove base shadow in light theme to avoid continuous dark band under the row
          // Add very subtle hover shadow only
          "px-4 py-2 cursor-pointer select-none transition-colors shadow-none hover:shadow-[0_6px_16px_rgba(0,0,0,0.08)] dark:hover:shadow-[0_8px_20px_rgba(0,0,0,0.45)]",
          active && "ring-2 ring-primary/50",
          className
        )}
      >
        <div {...props} className="flex items-center gap-2">
          <span className={cn("h-2 w-2 rounded-full", statusColor)} />
          <span className={cn("text-sm", active ? "text-text-primary" : "text-text-secondary")}>{title}</span>
        </div>
      </GlassCard>
    )
  }
)

TrackChip.displayName = "TrackChip"

export default TrackChip


