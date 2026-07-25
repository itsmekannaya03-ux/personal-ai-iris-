import React, { useState, useRef, useEffect } from 'react'

export default function ChatInput({ onSend, disabled, status }) {
  const [text, setText] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    if (!disabled) textareaRef.current?.focus()
  }, [disabled])

  const handleSubmit = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleInput = (e) => {
    setText(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px'
  }

  const placeholder = status === 'disconnected'
    ? 'Backend offline — start the server first...'
    : 'Message Iris...'

  return (
    <div className="input-row">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        disabled={disabled || status === 'disconnected'}
      />
      <button onClick={handleSubmit} disabled={!text.trim() || disabled || status === 'disconnected'}>
        Send
      </button>
    </div>
  )
}
