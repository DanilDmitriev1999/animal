"use client"

import * as React from "react"
import { GlassCard } from "@/components/ui/GlassCard"
import { Button } from "@/components/ui/button"
import { Send } from "lucide-react"
import { cn } from "@/lib/utils"
import { QuickCommandBtn } from "@/components/ui/QuickCommandBtn"

export interface ChatComposerProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  value: string
  placeholder?: string
  onChange: (value: string) => void
  onSend: (value: string) => void
  quickCommands?: { id: string; label: string }[]
}

// AICODE-NOTE: Unified chat composer with auto-sizing textarea and quick commands. Safe-area aware.
export const ChatComposer = React.forwardRef<HTMLDivElement, ChatComposerProps>(
  (
    { className, value, placeholder, onChange, onSend, quickCommands = [], ...props },
    ref
  ) => {
    const textareaRef = React.useRef<HTMLTextAreaElement | null>(null)

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        const trimmed = value.trim()
        if (trimmed) onSend(trimmed)
      }
    }

    const autoResize = () => {
      const el = textareaRef.current
      if (!el) return
      el.style.height = "auto"
      el.style.height = `${Math.min(160, el.scrollHeight)}px`
    }

    React.useEffect(() => {
      autoResize()
    }, [value])

    return (
      <div ref={ref} className={cn("w-full", className)} {...props}>
        <GlassCard className="p-2">
          <div className="flex flex-col gap-2">
            <div className="flex items-end gap-2">
              <textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                rows={1}
                className={cn(
                  "min-h-[40px] max-h-[160px] w-full resize-none bg-transparent text-base leading-6 text-text-primary placeholder:text-text-secondary focus:outline-none",
                  "rounded-input px-3 py-2 border border-transparent focus:border-white/20"
                )}
              />
              <Button size="icon" aria-label="Отправить сообщение" onClick={() => value.trim() && onSend(value.trim())}>
                <Send className="h-5 w-5" />
              </Button>
            </div>
            {/* AICODE-NOTE: Quick commands hidden by request */}
          </div>
        </GlassCard>
        <div style={{ paddingBottom: "env(safe-area-inset-bottom)" }} />
      </div>
    )
  }
)
ChatComposer.displayName = "ChatComposer"

export default ChatComposer


