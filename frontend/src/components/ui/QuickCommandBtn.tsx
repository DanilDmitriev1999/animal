import * as React from "react"
import { cn } from "@/lib/utils"

export interface QuickCommandBtnProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label: string
}

const QuickCommandBtn = React.forwardRef<
  HTMLButtonElement,
  QuickCommandBtnProps
>(({ className, label, ...props }, ref) => {
  return (
    <button
      ref={ref}
      className={cn(
        "rounded-input border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-text-secondary transition-colors hover:bg-white/10",
        className
      )}
      {...props}
    >
      {label}
    </button>
  )
})
QuickCommandBtn.displayName = "QuickCommandBtn"

export { QuickCommandBtn } 