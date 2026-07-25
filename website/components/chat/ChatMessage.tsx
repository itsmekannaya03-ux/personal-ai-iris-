"use client"

import { cn } from "@/lib/utils"
import { Bot, User, Check, Copy } from "lucide-react"
import { useState } from "react"

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  timestamp?: Date
}

export function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const isUser = role === "user"

  async function handleCopy() {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={cn("flex gap-3 group", isUser ? "flex-row-reverse" : "flex-row")}>
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold",
          isUser
            ? "bg-igris-600/30 text-igris-400 border border-igris-500/20"
            : "bg-white/10 text-white border border-white/10"
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      <div className={cn("flex flex-col max-w-[75%]", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
            isUser
              ? "bg-igris-600/20 border border-igris-500/20 text-white rounded-tr-sm"
              : "bg-white/5 border border-white/10 text-white/90 rounded-tl-sm"
          )}
        >
          {content}
        </div>

        <div className="flex items-center gap-2 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleCopy}
            className="text-white/30 hover:text-white/60 transition-colors"
            title="Copy message"
          >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
          </button>
          {timestamp && (
            <span className="text-[10px] text-white/20">
              {timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
