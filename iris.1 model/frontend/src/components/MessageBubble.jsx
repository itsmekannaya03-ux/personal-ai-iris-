import React from 'react'

export default function MessageBubble({ role, text, proactive, emotion, stage }) {
  const displayText = typeof text === 'string'
    ? text
    : (typeof text === 'object' && text !== null ? (text.message || JSON.stringify(text)) : String(text || ''))

  return (
    <div className={`message ${role} ${proactive ? 'proactive-msg' : ''}`}>
      <div className="sender">
        {role === 'user' ? 'You' : (
          <span>
            Iris {proactive && <span className="proactive-tag">⚡ Vision: {emotion || 'detected'} (Stage {stage})</span>}
          </span>
        )}
      </div>
      <div className="bubble">{displayText}</div>
    </div>
  )
}
