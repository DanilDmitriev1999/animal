'use client'

import * as React from "react"
import { GlassCard } from "./GlassCard"
import { cn } from "@/lib/utils"
import { motion } from "framer-motion"

export interface TrackCardProps {
  title: string
  description: string
  progress: number
  className?: string
}

const TrackCard = React.forwardRef<HTMLDivElement, TrackCardProps>(
  ({ title, description, progress, className }, ref) => {
    return (
      <GlassCard ref={ref} className={cn("p-6", className)}>
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-text-primary">{title}</h3>
        </div>
        <p className="mb-4 text-sm text-text-secondary">{description}</p>
        <div className="flex items-center gap-2">
            <div className="w-full h-1 rounded-full bg-white/10 overflow-hidden">
                <motion.div
                    className="h-full rounded-full bg-primary"
                    initial={{ width: "0%" }}
                    whileInView={{ width: `${progress}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    viewport={{ once: true }}
                />
            </div>
          <span className="text-xs font-mono text-text-secondary">{progress}%</span>
        </div>
      </GlassCard>
    )
  }
)
TrackCard.displayName = "TrackCard"

export { TrackCard } 