import React, { useState, useRef, useEffect, useCallback } from 'react'
import ChatBox from './components/ChatBox'
import ChatInput from './components/ChatInput'
import StatusBar from './components/StatusBar'
import VisionPanel from './components/VisionPanel'
import TodoPanel from './components/TodoPanel'
import { chat, getStatus, clearConversationSession, getProactiveEvents, stopVoice } from './api'

export default function App() {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem('iris_chat_history')
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed.map(m => ({
            ...m,
            text: typeof m.text === 'string'
              ? m.text
              : (typeof m.text === 'object' && m.text !== null ? (m.text.message || JSON.stringify(m.text)) : String(m.text || ''))
          }))
        }
      }
    } catch {}
    return [
      { role: 'assistant', text: 'Good day. I am Iris, your personal AI assistant. How may I help you?' },
    ]
  })
  const [status, setStatus] = useState('connecting')
  const [voiceOn, setVoiceOn] = useState(true)
  const [thinking, setThinking] = useState(false)
  const [visionOn, setVisionOn] = useState(true)
  const [todoOn, setTodoOn] = useState(false)
  const messagesEndRef = useRef(null)
  const lastProactiveIdRef = useRef(null)
  const seenEventIdsRef = useRef(new Set())

  useEffect(() => {
    try {
      localStorage.setItem('iris_chat_history', JSON.stringify(messages.slice(-100)))
    } catch {}
  }, [messages])

  useEffect(() => {
    let alive = true
    const check = () => {
      getStatus()
        .then(() => { if (alive) setStatus('connected') })
        .catch(() => { if (alive) setStatus('disconnected') })
    }
    check()
    const t = setInterval(check, 4000)
    return () => { alive = false; clearInterval(t) }
  }, [])

  const [isSpeaking, setIsSpeaking] = useState(false)
  const queueRef = useRef([])
  const isProcessingRef = useRef(false)
  const speakPollRef = useRef(null)

  const monitorSpeaking = useCallback(() => {
    if (speakPollRef.current) {
      clearInterval(speakPollRef.current)
    }
    setIsSpeaking(true)
    let pollCount = 0
    speakPollRef.current = setInterval(async () => {
      pollCount++
      try {
        const st = await getStatus()
        if (!st.speaking && pollCount > 1) {
          clearInterval(speakPollRef.current)
          speakPollRef.current = null
          setTimeout(() => setIsSpeaking(false), 100)
        }
      } catch {
        clearInterval(speakPollRef.current)
        speakPollRef.current = null
        setIsSpeaking(false)
      }
      if (pollCount > 600) {
        clearInterval(speakPollRef.current)
        speakPollRef.current = null
        setIsSpeaking(false)
      }
    }, 350)
  }, [])

  // Continuous Proactive Event Listener for Facial Emotion & Geometric Reactions
  useEffect(() => {
    let alive = true
    let isPolling = false

    const pollProactive = async () => {
      if (isPolling) return
      isPolling = true
      try {
        const lastId = lastProactiveIdRef.current
        const data = await getProactiveEvents(lastId)
        if (!alive || !data || !data.events) return
        if (data.events.length > 0) {
          data.events.forEach(evt => {
            if (!evt || !evt.id || seenEventIdsRef.current.has(evt.id)) return
            seenEventIdsRef.current.add(evt.id)
            lastProactiveIdRef.current = evt.id
            const msgText = typeof evt.message === 'string'
              ? evt.message
              : (typeof evt.message === 'object' && evt.message !== null ? evt.message.message : String(evt.message || ''))
            if (msgText) {
              setMessages(prev => [...prev, {
                role: 'assistant',
                text: msgText,
                proactive: true,
                emotion: evt.emotion,
                stage: evt.stage
              }])
              if (voiceOn) {
                monitorSpeaking()
              }
            }
          })
        }
      } catch {
      } finally {
        isPolling = false
      }
    }
    const t = setInterval(pollProactive, 1800)
    return () => { alive = false; clearInterval(t) }
  }, [voiceOn, monitorSpeaking])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const processNextInQueue = useCallback(async () => {
    if (isProcessingRef.current || queueRef.current.length === 0) return
    isProcessingRef.current = true
    setThinking(true)

    const item = queueRef.current.shift()
    const nextText = typeof item === 'object' ? item.text : item
    const isVoice = typeof item === 'object' ? Boolean(item.isVoice) : false
    setMessages(prev => [...prev, { role: 'user', text: nextText, isVoice }])

    try {
      const res = await chat(nextText, voiceOn, isVoice)
      const replyText = res.response || 'No response.'
      setMessages(prev => [...prev, { role: 'assistant', text: replyText }])

      if (voiceOn) {
        monitorSpeaking()
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Connection error. Please check the backend server.' }])
    } finally {
      setThinking(false)
      isProcessingRef.current = false
      // Process next queued message if any exists
      if (queueRef.current.length > 0) {
        setTimeout(processNextInQueue, 50)
      }
    }
  }, [voiceOn, monitorSpeaking])

  const handleSend = useCallback((text, isVoice = false) => {
    const trimmed = (text || '').trim()
    if (!trimmed) return
    queueRef.current.push({ text: trimmed, isVoice })
    processNextInQueue()
  }, [processNextInQueue])

  const handleNewSession = async () => {
    try {
      await clearConversationSession()
    } catch {}
    const fresh = [
      { role: 'assistant', text: 'New session started. How can I assist you today, Commander?' },
    ]
    setMessages(fresh)
    try {
      localStorage.setItem('iris_chat_history', JSON.stringify(fresh))
    } catch {}
  }

  const lastAssistantText = messages.filter(m => m.role === 'assistant').slice(-1)[0]?.text || ''

  const [isHearing, setIsHearing] = useState(false)

  const handleStopVoice = useCallback(async () => {
    if (speakPollRef.current) {
      clearInterval(speakPollRef.current)
      speakPollRef.current = null
    }
    try {
      await stopVoice()
    } catch {}
    setIsSpeaking(false)
  }, [])

  return (
    <div className={`app ${visionOn ? 'with-panel' : ''}`}>
      <header className="header">
        <div className="header-left">
          <span className="logo">IRIS</span>
          <span className="subtitle">AI Assistant</span>
        </div>
        <div className="header-right">
          <button
            type="button"
            className="session-reset-btn"
            onClick={handleNewSession}
            title="Start a fresh conversation (Iris remembers your permanent memories)"
          >
            🔄 New Chat
          </button>
          <button
            type="button"
            className={`todo-toggle ${todoOn ? 'on' : ''}`}
            onClick={() => setTodoOn(t => !t)}
            title="Tasks & Reminders (Layer 2 Memory)"
          >
            📋 Tasks
          </button>
          <button
            type="button"
            className={`vision-toggle ${visionOn ? 'on' : ''}`}
            onClick={() => setVisionOn(v => !v)}
            title="Show what Iris sees"
          >
            👁 Vision
          </button>
          <StatusBar
            status={status}
            voiceOn={voiceOn}
            onVoiceToggle={() => setVoiceOn(v => !v)}
            isSpeaking={isSpeaking}
            isHearing={isHearing}
          />
        </div>
      </header>
      <main className={`main ${visionOn || todoOn ? 'with-panel' : ''}`}>
        <ChatBox messages={messages} thinking={thinking} />
        {todoOn && <TodoPanel onClose={() => setTodoOn(false)} />}
        {visionOn && <VisionPanel onCommand={handleSend} />}
        <div ref={messagesEndRef} />
      </main>
      <footer className="footer">
        <ChatInput
          onSend={handleSend}
          disabled={thinking || isSpeaking}
          status={status}
          lastAssistantText={lastAssistantText}
          isSpeaking={isSpeaking}
          onStopVoice={handleStopVoice}
          onHearingChange={setIsHearing}
        />
      </footer>
    </div>
  )
}
