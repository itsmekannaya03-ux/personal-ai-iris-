"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { api } from "@/lib/api"
import { ChatMessage } from "@/components/chat/ChatMessage"
import { ChatInput } from "@/components/chat/ChatInput"
import { TokenBar } from "@/components/chat/TokenBar"
import { Bot, Terminal } from "lucide-react"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface ConvoStatus {
  tokens_used: number
  max_tokens: number
  ratio: number
  status: "ok" | "warning" | "critical"
  message: string
  message_count: number
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm IGRIS, your personal AI operating system. How can I help you today?",
      timestamp: new Date(),
    },
  ])
  const [loading, setLoading] = useState(false)
  const [convoStatus, setConvoStatus] = useState<ConvoStatus | null>(null)
  const [engineOnline, setEngineOnline] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const updateStatus = useCallback(async () => {
    try {
      const s = await api.chat.status()
      setConvoStatus(s)
    } catch {}
  }, [])

  useEffect(() => {
    api.chat.status().then(setConvoStatus).catch(() => {})
    fetch("/api/status")
      .then((r) => r.ok && setEngineOnline(true))
      .catch(() => {})
    const interval = setInterval(updateStatus, 5000)
    return () => clearInterval(interval)
  }, [updateStatus])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function handleSend(input: string) {
    const userMsg: Message = { role: "user", content: input, timestamp: new Date() }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await api.chat.send(input)
      const assistantMsg: Message = {
        role: "assistant",
        content: res.response,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
      await updateStatus()
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I couldn't reach the engine. Make sure IGRIS is running.",
          timestamp: new Date(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  async function handleNewSession() {
    try {
      await api.chat.newSession()
      setMessages([
        {
          role: "assistant",
          content: "Session reset. How can I help you?",
          timestamp: new Date(),
        },
      ])
      await updateStatus()
    } catch {}
  }

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Bot className="w-5 h-5 text-igris-400" />
            Chat
          </h1>
          <p className="text-xs text-white/40 mt-0.5">
            {engineOnline ? (
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block" />
                Engine online
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-500 inline-block" />
                Engine offline
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-white/30">
          <Terminal className="w-3 h-3" />
          <span>/session, /voice, /mode, /memory...</span>
        </div>
      </div>

      {convoStatus && (
        <div className="mb-3">
          <TokenBar
            tokensUsed={convoStatus.tokens_used}
            maxTokens={convoStatus.max_tokens}
            ratio={convoStatus.ratio}
            status={convoStatus.status}
            message={convoStatus.message}
            messageCount={convoStatus.message_count}
            onNewSession={handleNewSession}
          />
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-4 pr-2 scrollbar-thin">
        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-white/10 border border-white/10 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white/50" />
            </div>
            <div className="flex items-center gap-1.5 px-4 py-3 rounded-2xl bg-white/5 border border-white/10">
              <span className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="mt-4">
        <ChatInput onSend={handleSend} disabled={loading} />
      </div>
    </div>
  )
}
