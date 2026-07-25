import React from 'react'

export default function MessageBubble({ role, text }) {
  return (
    <div className={`message ${role}`}>
      <div className="sender">{role === 'user' ? 'You' : 'Iris'}</div>
      <div className="bubble">{text}</div>
    </div>
  )
}
