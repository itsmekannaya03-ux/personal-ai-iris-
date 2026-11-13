import React from 'react'

export default function StatusBar({ status, voiceOn, onVoiceToggle, isSpeaking = false, isHearing = false }) {
  const label = status === 'connected' ? 'Online' : status === 'disconnected' ? 'Offline' : 'Connecting...'

  return (
    <div className="status-bar">
      <span className={`status-dot ${status}`}></span>
      <span>{label}</span>
      {isSpeaking ? (
        <span className="mic-indicator-badge muted" title="Iris is speaking — input mic is OFF to eliminate echo">
          <span className="mic-dot-off"></span> 🔇 Input Mic OFF (Iris Speaking)
        </span>
      ) : isHearing ? (
        <span className="mic-indicator-badge hearing" title="You are speaking — output sound is OFF">
          <span className="mic-dot-live" style={{ background: '#ef4444' }}></span> 🔴 You Speaking (Output OFF)
        </span>
      ) : (
        <span className="mic-indicator-badge" title="Input microphone is live — speak anytime!">
          <span className="mic-dot-live"></span> 🎤 Mic Live
        </span>
      )}
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
