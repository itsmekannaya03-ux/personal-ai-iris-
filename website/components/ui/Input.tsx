import { cn } from "@/lib/utils"
import { forwardRef, type InputHTMLAttributes } from "react"

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  labelClassName?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", label, labelClassName, error, id, style, ...props }, ref) => {
    const hasBg = className.includes("bg-")
    const hasText = className.includes("text-")
    const hasBorder = className.includes("border")
    const hasFocus = className.includes("focus:")

    const isLightWhite = className.includes("text-white") || className.includes("text-slate-100") || className.includes("text-slate-50")
    const isLightBlue = className.includes("text-cyan") || className.includes("text-sky") || className.includes("text-blue")
    const computedColor = style?.color ? style.color : isLightBlue ? "#67e8f9" : isLightWhite ? "#f1f5f9" : "#000000"

    return (
      <div className="space-y-1.5 text-left">
        {label && (
          <label htmlFor={id} className={cn("block text-xs font-bold uppercase tracking-wider text-black", labelClassName)}>
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          style={{ color: computedColor, WebkitTextFillColor: computedColor, ...style }}
          className={cn(
            "w-full rounded-xl px-4 py-3.5 text-sm transition-all shadow-sm",
            !hasBorder && "border-2 border-slate-900",
            !hasBg && "bg-white",
            !hasText && "text-black placeholder:text-slate-500 font-semibold caret-black",
            !hasFocus && "focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black",
            error && "border-red-500 focus:border-red-500 focus:ring-red-500/20",
            className
          )}
          {...props}
        />
        {error && <p className="text-xs text-red-500 font-medium">{error}</p>}
      </div>
    )
  }
)
Input.displayName = "Input"

export { Input }
