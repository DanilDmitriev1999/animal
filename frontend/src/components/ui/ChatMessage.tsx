import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import Image from "next/image"
import { BotIcon } from "lucide-react"

const chatMessageVariants = cva("flex items-start gap-3", {
  variants: {
    role: {
      user: "justify-end",
      assistant: "justify-start",
    },
  },
  defaultVariants: {
    role: "assistant",
  },
})

const bubbleVariants = cva("rounded-2xl px-4 py-3 max-w-prose", {
      variants: {
      role: {
        user: "bg-primary text-primary-foreground rounded-br-md",
        assistant: "bg-secondary text-secondary-foreground rounded-bl-md",
      },
    },
  defaultVariants: {
    role: "assistant",
  },
})

export interface ChatMessageProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "role">,
    VariantProps<typeof chatMessageVariants> {
  avatarUrl?: string
  message: string
}

const ChatMessage = React.forwardRef<HTMLDivElement, ChatMessageProps>(
  ({ className, role, avatarUrl, message, ...props }, ref) => {
    const UserAvatar = () =>
      avatarUrl ? (
        <Image
          src={avatarUrl}
          alt="User avatar"
          width={32}
          height={32}
          className="rounded-full"
        />
      ) : null

    const AssistantAvatar = () => (
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary">
        <BotIcon className="h-5 w-5 text-secondary-foreground" />
      </div>
    )

    return (
      <div
        ref={ref}
        className={cn(chatMessageVariants({ role }), className)}
        {...props}
      >
        {role === "assistant" && <AssistantAvatar />}
        <div className={cn(bubbleVariants({ role }))}>
          <p className="text-sm leading-relaxed">{message}</p>
        </div>
        {role === "user" && <UserAvatar />}
      </div>
    )
  }
)
ChatMessage.displayName = "ChatMessage"

export { ChatMessage } 