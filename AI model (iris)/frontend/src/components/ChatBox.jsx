import React from 'react'
import MessageBubble from './MessageBubble'

export default function ChatBox({ messages, thinking }) {
  return (
    <div className="chat-box">
      {messages.map((msg, i) => (
        <MessageBubble key={i} role={msg.role} text={msg.text} />
      ))}
      {thinking && (
        <div className="typing">
          <span></span><span></span><span></span>
        </div>
      )}
    </div>
  )
}
