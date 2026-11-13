import { cn } from "@/lib/utils"
import type { HTMLAttributes } from "react"

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "glow"
}

export function Card({ className, variant = "default", children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-white/10 bg-white/[0.02] backdrop-blur-sm",
        variant === "glow" && "glow",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
