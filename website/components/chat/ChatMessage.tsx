"use client"

import { cn } from "@/lib/utils"
import { Bot, User, Check, Copy, Terminal, Sparkles } from "lucide-react"
import { useState } from "react"

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  timestamp?: Date
}

function CodeBlock({ code, lang }: { code: string; lang: string }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(code.trim())
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="my-2.5 rounded-xl border border-cyan-500/30 bg-[#080a14] overflow-hidden shadow-lg shadow-cyan-950/20">
      <div className="flex items-center justify-between px-3 py-1.5 bg-white/[0.04] border-b border-white/10 text-xs font-mono text-cyan-300">
        <span className="flex items-center gap-1.5">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          {lang ? lang.toUpperCase() : "TERMINAL COMMAND"}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition-colors text-[11px]"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-300 font-semibold">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy Command</span>
            </>
          )}
        </button>
      </div>
      <div className="p-3 overflow-x-auto text-xs font-mono text-cyan-100 bg-black/40 select-all whitespace-pre leading-relaxed">
        {code.trim()}
      </div>
    </div>
  )
}

export function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const isUser = role === "user"

  async function handleCopy() {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Parse code blocks vs regular text
  const parts = content.split(/(```[\s\S]*?```)/g)

  return (
    <div className={cn("flex gap-3 group", isUser ? "flex-row-reverse" : "flex-row")}>
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold shadow-md",
          isUser
            ? "bg-gradient-to-br from-cyan-600 to-blue-700 text-white border border-cyan-400/30"
            : "bg-[#0f1322] text-cyan-300 border border-cyan-500/30"
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4 text-cyan-400" />}
      </div>

      <div className={cn("flex flex-col max-w-[85%]", isUser ? "items-end" : "items-start")}>
        <div className="flex items-center gap-1.5 px-1 mb-1 text-[11px] font-semibold tracking-wide">
          {isUser ? (
            <span className="text-white/50">You</span>
          ) : (
            <span className="text-cyan-400 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-cyan-300" />
              REN &bull; Architect
            </span>
          )}
        </div>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-gradient-to-r from-cyan-900/40 to-blue-900/40 border border-cyan-500/30 text-white rounded-tr-sm"
              : "bg-[#0b0e1b]/80 border border-white/10 text-white/90 rounded-tl-sm backdrop-blur-md"
          )}
        >
          {parts.map((part, index) => {
            if (part.startsWith("```") && part.endsWith("```")) {
              const lines = part.slice(3, -3).trim().split("\n")
              let lang = ""
              let code = lines.join("\n")
              if (lines[0] && !lines[0].includes(" ") && lines.length > 1) {
                lang = lines[0]
                code = lines.slice(1).join("\n")
              }
              return <CodeBlock key={index} code={code} lang={lang} />
            }
            return (
              <span key={index} className="whitespace-pre-wrap">
                {part}
              </span>
            )
          })}
        </div>

        <div className="flex items-center gap-2 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleCopy}
            className="text-white/30 hover:text-white/60 transition-colors"
            title="Copy message"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
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
