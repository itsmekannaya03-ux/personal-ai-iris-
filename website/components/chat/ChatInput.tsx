"use client"

import { useState, useRef, type KeyboardEvent } from "react"
import { Send, CornerDownLeft } from "lucide-react"

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({ onSend, disabled, placeholder = "Message IRIS..." }: ChatInputProps) {
  const [input, setInput] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function handleSubmit() {
    const trimmed = input.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setInput("")
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  function handleInput() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  return (
    <div className="flex items-end gap-2 bg-white/[0.02] border border-white/10 rounded-2xl px-4 py-3 focus-within:border-iris-500/50 focus-within:ring-1 focus-within:ring-iris-500/20 transition-all">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="flex-1 bg-transparent text-sm text-white placeholder-white/30 resize-none outline-none max-h-40 leading-relaxed disabled:opacity-50"
      />

      <div className="flex items-center gap-1 flex-shrink-0">
        <span className="hidden sm:flex items-center gap-1 text-[10px] text-white/20 mr-1">
          <CornerDownLeft className="w-3 h-3" />
          Send
        </span>
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || disabled}
          className="w-8 h-8 rounded-lg bg-iris-600 hover:bg-iris-500 disabled:bg-white/5 disabled:text-white/20 text-white flex items-center justify-center transition-all disabled:cursor-not-allowed"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
