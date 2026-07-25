"use client"

import { cn } from "@/lib/utils"
import { AlertTriangle, RefreshCw } from "lucide-react"

interface TokenBarProps {
  tokensUsed: number
  maxTokens: number
  ratio: number
  status: "ok" | "warning" | "critical"
  message: string
  messageCount: number
  onNewSession: () => void
}

export function TokenBar({
  tokensUsed,
  maxTokens,
  ratio,
  status,
  message,
  messageCount,
  onNewSession,
}: TokenBarProps) {
  const pct = Math.round(ratio * 100)

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-white/[0.02] border border-white/10 rounded-xl">
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/40 font-medium">Context</span>
            {status !== "ok" && (
              <AlertTriangle
                className={cn(
                  "w-3 h-3",
                  status === "warning" ? "text-yellow-500" : "text-red-500"
                )}
              />
            )}
          </div>
          <span className="text-[11px] text-white/30">
            {tokensUsed}/{maxTokens} tokens &middot; {messageCount} messages
          </span>
        </div>
        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-500",
              status === "ok" && "bg-igris-500",
              status === "warning" && "bg-yellow-500",
              status === "critical" && "bg-red-500"
            )}
            style={{ width: `${Math.min(pct, 100)}%` }}
          />
        </div>
        {message && (
          <p className="text-[10px] text-white/30 mt-0.5">{message}</p>
        )}
      </div>

      <button
        onClick={onNewSession}
        className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 text-xs text-white/40 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
        title="Start new session"
      >
        <RefreshCw className="w-3 h-3" />
        New
      </button>
    </div>
  )
}
