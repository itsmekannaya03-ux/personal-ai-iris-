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
          "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-75 active:scale-[0.98] select-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-iris-500/50 disabled:opacity-50 disabled:pointer-events-none touch-manipulation",
          {
            "bg-iris-600 hover:bg-iris-500 active:bg-iris-700 text-white shadow-lg shadow-iris-600/25": variant === "primary",
            "bg-white/5 hover:bg-white/10 active:bg-white/15 text-white border border-white/10": variant === "secondary",
            "hover:bg-white/5 active:bg-white/10 text-white/70 hover:text-white": variant === "ghost",
            "border border-iris-500/50 text-iris-400 hover:bg-iris-500/10 active:bg-iris-500/20": variant === "outline",
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
