import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

// AICODE-NOTE: Enhanced glass card variants with better theme support
const glassCardVariants = cva(
  "backdrop-blur-[10px] border transition-all duration-300",
  {
    variants: {
      shape: {
        // AICODE-NOTE: Slightly smaller radius to enhance floating feel
        card: "rounded-[24px]",
        pill: "rounded-full",
        none: "rounded-none",
      },
      variant: {
        default: "glass-morphism",
        strong: "glass-morphism bg-opacity-80 dark:bg-opacity-10",
        subtle: "backdrop-blur-[12px] bg-white/10 dark:bg-white/5 border-white/20 dark:border-white/10",
        // AICODE-NOTE: Neumorphic surface (no glass). Subtle even drop shadow; no white glow in dark theme.
        neumorph:
          // AICODE-NOTE: Уменьшены радиусы тени для тесного контейнера сайдбара
          "bg-white dark:bg-[#0F141A] border border-black/5 dark:border-white/5 shadow-[0_4px_12px_rgba(0,0,0,0.10)] dark:shadow-[0_6px_18px_rgba(0,0,0,0.45)]",
      },
      size: {
        default: "",
        sm: "p-4",
        md: "p-6", 
        lg: "p-8",
      }
    },
    defaultVariants: {
      shape: "card",
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
        className={cn(glassCardVariants({ ...(props as any), variant, size }), className)}
        ref={ref}
        {...props}
      />
    )
  }
)
GlassCard.displayName = "GlassCard"

export { GlassCard, glassCardVariants } 