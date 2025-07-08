import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

// AICODE-NOTE: Enhanced glass card variants with better theme support
const glassCardVariants = cva(
  "backdrop-blur-[10px] rounded-[34px] border transition-all duration-300",
  {
    variants: {
      variant: {
        default: "glass-morphism",
        strong: "glass-morphism bg-opacity-80 dark:bg-opacity-10",
        subtle: "backdrop-blur-[12px] bg-white/10 dark:bg-white/5 border-white/20 dark:border-white/10",
      },
      size: {
        default: "",
        sm: "p-4",
        md: "p-6", 
        lg: "p-8",
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface GlassCardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof glassCardVariants> {
  asChild?: boolean
}

const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "div"
    return (
      <Comp
        className={cn(glassCardVariants({ variant, size }), className)}
        ref={ref}
        {...props}
      />
    )
  }
)
GlassCard.displayName = "GlassCard"

export { GlassCard, glassCardVariants } 