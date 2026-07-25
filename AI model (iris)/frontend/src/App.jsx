import React, { useState, useRef, useEffect, useCallback } from 'react'
import ChatBox from './components/ChatBox'
import ChatInput from './components/ChatInput'
import StatusBar from './components/StatusBar'
import { chat, getStatus } from './api'

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Good day. I am Iris, your personal AI assistant. How may I help you?' },
  ])
  const [status, setStatus] = useState('connecting')
  const [voiceOn, setVoiceOn] = useState(false)
  const [thinking, setThinking] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    getStatus()
      .then(() => setStatus('connected'))
      .catch(() => setStatus('disconnected'))
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(async (text) => {
    setMessages(prev => [...prev, { role: 'user', text }])
    setThinking(true)
    try {
      const res = await chat(text, voiceOn)
      setMessages(prev => [...prev, { role: 'assistant', text: res.text || 'No response.' }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Connection error. Please check the backend server.' }])
    } finally {
      setThinking(false)
    }
  }, [voiceOn])

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <span className="logo">IRIS</span>
          <span className="subtitle">AI Assistant</span>
        </div>
        <div className="header-right">
          <StatusBar status={status} voiceOn={voiceOn} onVoiceToggle={() => setVoiceOn(v => !v)} />
        </div>
      </header>
      <main className="main">
        <ChatBox messages={messages} thinking={thinking} />
        <div ref={messagesEndRef} />
      </main>
      <footer className="footer">
        <ChatInput onSend={handleSend} disabled={thinking} status={status} />
      </footer>
    </div>
  )
}
