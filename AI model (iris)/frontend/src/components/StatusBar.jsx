import React from 'react'

export default function StatusBar({ status, voiceOn, onVoiceToggle }) {
  const label = status === 'connected' ? 'Online' : status === 'disconnected' ? 'Offline' : 'Connecting...'

  return (
    <div className="status-bar">
      <span className={`status-dot ${status}`}></span>
      <span>{label}</span>
      <button
        className={`voice-toggle ${voiceOn ? 'active' : ''}`}
        onClick={onVoiceToggle}
        title="Toggle voice response"
      >
        <span>{voiceOn ? '🔊' : '🔇'}</span>
        <span>Voice</span>
      </button>
    </div>
  )
}
