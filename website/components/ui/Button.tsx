import { cn } from "@/lib/utils"
import { forwardRef, type ButtonHTMLAttributes } from "react"

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "outline"
  size?: "sm" | "md" | "lg"
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-igris-500/50 disabled:opacity-50 disabled:pointer-events-none",
          {
            "bg-igris-600 hover:bg-igris-500 text-white glow": variant === "primary",
            "bg-white/5 hover:bg-white/10 text-white border border-white/10": variant === "secondary",
            "hover:bg-white/5 text-white/70 hover:text-white": variant === "ghost",
            "border border-igris-500/50 text-igris-400 hover:bg-igris-500/10": variant === "outline",
          },
          {
            "px-3 py-1.5 text-sm": size === "sm",
            "px-5 py-2.5 text-sm": size === "md",
            "px-8 py-3 text-base": size === "lg",
          },
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)
Button.displayName = "Button"

export { Button }
