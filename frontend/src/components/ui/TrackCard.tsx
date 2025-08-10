'use client'

import * as React from "react"
import { GlassCard } from "./GlassCard"
import { cn } from "@/lib/utils"
import { motion } from "framer-motion"

export interface TrackCardProps {
  title: string
  description: string
  className?: string
  size?: "sm" | "md" | "lg"
  showProgress?: boolean
}

const TrackCard = React.forwardRef<HTMLDivElement, TrackCardProps>(
  ({ title, description, className, size = "lg", showProgress = false }, ref) => {
    return (
      <GlassCard ref={ref} size={size as any} className={cn("p-0", className)}>
        <div className="p-6 sm:p-7 lg:p-8">
          <div className="mb-3 sm:mb-4">
            <h3 className="text-xl sm:text-[22px] font-semibold leading-snug text-text-primary">{title}</h3>
          </div>
          <p className="mb-4 sm:mb-6 text-[13px] sm:text-sm text-text-secondary line-clamp-3">{description}</p>

          {showProgress && (
            <div className="flex items-center gap-2">
              <div className="w-full h-1 rounded-full bg-white/10 overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-primary"
                  initial={{ width: "0%" }}
                  whileInView={{ width: `0%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  viewport={{ once: true }}
                />
              </div>
              <span className="text-xs font-mono text-text-secondary">0%</span>
            </div>
          )}
        </div>
      </GlassCard>
    )
  }
)
TrackCard.displayName = "TrackCard"

export { TrackCard } 