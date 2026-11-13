import React, { useEffect, useState } from 'react'
import { getVisionLast, getProactiveEvents, simulateEmotion, getCameraDevices, switchCamera, resetPresence, reEnrollFace, getPresenceHudState } from '../api'

const KIND_LABELS = {
  camera: '📷 Camera',
  screen: '🖥 Screen',
  ocr: '📝 OCR',
  faces: '👤 Faces',
  ui: '🧩 UI',
}

function timeAgo(seconds) {
  if (seconds < 5) return 'just now'
  if (seconds < 60) return `${Math.round(seconds)}s ago`
  return `${Math.round(seconds / 60)}m ago`
}

export default function VisionPanel({ onCommand }) {
  const [events, setEvents] = useState([])
  const [previewOn, setPreviewOn] = useState(true)
  const [previewError, setPreviewError] = useState(false)
  const [error, setError] = useState('')
  const [currentEmotion, setCurrentEmotion] = useState('neutral')
  const [confidence, setConfidence] = useState(0)
  const [activeAction, setActiveAction] = useState('')
  const [escalationStage, setEscalationStage] = useState(0)
  const [isSimulating, setIsSimulating] = useState(false)
  const [activeCamera, setActiveCamera] = useState(0)
  const [availableCameras, setAvailableCameras] = useState([0])
  const [streamKey, setStreamKey] = useState(Date.now())
  const [hudState, setHudState] = useState(null)
  const [biometricStatus, setBiometricStatus] = useState('')
  const [isEnrolling, setIsEnrolling] = useState(false)

  // One-time camera discovery on mount (prevents hardware camera cycling)
  useEffect(() => {
    let alive = true
    getCameraDevices()
      .then((cdata) => {
        if (alive && cdata) {
          if (cdata.active_camera !== undefined) setActiveCamera(cdata.active_camera)
          if (Array.isArray(cdata.available_cameras) && cdata.available_cameras.length > 0) {
            setAvailableCameras(cdata.available_cameras)
          }
        }
      })
      .catch(() => {})
    return () => { alive = false }
  }, [])

  useEffect(() => {
    let alive = true
    let isPolling = false

    const poll = async () => {
      if (isPolling) return
      isPolling = true

      try {
        const [vRes, pRes, hRes] = await Promise.allSettled([
          getVisionLast(),
          getProactiveEvents(0),
          getPresenceHudState(),
        ])

        if (!alive) return

        if (vRes.status === 'fulfilled' && vRes.value) {
          setEvents(vRes.value.events || [])
          setError('')
        } else if (vRes.status === 'rejected') {
          setError('Vision feed unavailable — is the backend running?')
        }

        if (pRes.status === 'fulfilled' && pRes.value?.current_state) {
          const st = pRes.value.current_state
          setCurrentEmotion(st.emotion || 'neutral')
          setConfidence(Math.round((st.confidence || 0) * 100))
          const rawAct = st.active_action
          const actStr = typeof rawAct === 'object' && rawAct !== null ? (rawAct.message || '') : (typeof rawAct === 'string' ? rawAct : '')
          setActiveAction(actStr)
          setEscalationStage(st.escalation_stage || 0)
        }

        if (hRes.status === 'fulfilled' && hRes.value) {
          setHudState(hRes.value)
        }
      } catch {
        // silent fail
      } finally {
        isPolling = false
      }
    }

    poll()
    const t = setInterval(poll, 2500)
    return () => { alive = false; clearInterval(t) }
  }, [])

  const handleSwitchCamera = async () => {
    const list = availableCameras.length > 0 ? availableCameras : [1, 0]
    const currentIdx = list.indexOf(activeCamera)
    const nextCam = list[(currentIdx + 1) % list.length]
    try {
      await switchCamera(nextCam)
      setActiveCamera(nextCam)
      setPreviewError(false)
      setStreamKey(Date.now())
    } catch (e) {
      console.error('Camera switch error:', e)
    }
  }

  const handleSimulate = async (emotion) => {
    setIsSimulating(true)
    try {
      await simulateEmotion(emotion)
    } finally {
      setTimeout(() => setIsSimulating(false), 500)
    }
  }

  const handleRegisterNew = async () => {
    setIsEnrolling(true)
    setBiometricStatus('Scanning face & enrolling parameters as Commander...')
    try {
      const res = await reEnrollFace('Commander')
      setBiometricStatus(res.message || 'Face registered successfully as Commander!')
      const hdata = await getPresenceHudState()
      if (hdata) setHudState(hdata)
      setTimeout(() => setBiometricStatus(''), 5000)
    } catch (e) {
      setBiometricStatus('Enrollment failed: Please look directly into the camera.')
      setTimeout(() => setBiometricStatus(''), 5000)
    } finally {
      setIsEnrolling(false)
    }
  }

  const handleResetFace = async () => {
    try {
      const res = await resetPresence()
      setBiometricStatus(res.message || 'Previous face profile removed. Ready for new registration.')
      const hdata = await getPresenceHudState()
      if (hdata) setHudState(hdata)
      setTimeout(() => setBiometricStatus(''), 5000)
    } catch (e) {
      setBiometricStatus('Failed to reset face profile.')
      setTimeout(() => setBiometricStatus(''), 4000)
    }
  }

  const emotionColor = {
    sad: '#ff7b72',
    sadness: '#ff7b72',
    joy: '#7ee787',
    anger: '#f85149',
    surprise: '#e3b341',
    fear: '#bc8cff',
    fatigue: '#d2a8ff',
    disgust: '#7ee787',
    neutral: '#58a6ff'
  }[currentEmotion] || '#58a6ff'

  return (
    <aside className="vision-panel">
      <div className="vision-panel-header">
        <span className="vision-panel-title">👁 Iris&apos;s Vision</span>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <button
            type="button"
            className="preview-toggle"
            style={{ fontSize: '11px', padding: '3px 8px' }}
            onClick={handleSwitchCamera}
            title={`Active: Camera ${activeCamera}. Click to switch camera device.`}
          >
            📷 Cam {activeCamera}
          </button>
          <button
            type="button"
            className={`preview-toggle ${previewOn ? 'on' : ''}`}
            onClick={() => { setPreviewOn(v => !v); setPreviewError(false); setStreamKey(Date.now()); }}
            title={previewOn ? 'Live camera feed ON — click to stop' : 'Live camera feed OFF — click to start'}
          >
            {previewOn ? '● LIVE' : '○ PAUSED'}
          </button>
        </div>
      </div>

      <div className="vision-preview">
        {previewOn ? (
          <>
            {!previewError && (
              <img
                key={streamKey}
                src={`/api/vision/preview?key=${streamKey}`}
                alt="Live camera feed"
                className="vision-preview-img"
                onError={() => setPreviewError(true)}
              />
            )}
            {previewError && (
              <div className="vision-preview-fallback">
                <p>📷 Camera preview connecting...</p>
                <button
                  type="button"
                  style={{
                    marginTop: '8px',
                    fontSize: '11px',
                    padding: '4px 10px',
                    background: '#1f293d',
                    border: '1px solid #38bdf8',
                    color: '#38bdf8',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                  onClick={() => { setPreviewError(false); setStreamKey(Date.now()); handleSwitchCamera(); }}
                >
                  🔄 Switch / Retry Camera
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="vision-preview-fallback">
            <p>Live feed paused</p>
          </div>
        )}
      </div>

      {/* Real-time Facial Geometry & Emotion Detection HUD */}
      <div className="vision-emotion-hud" style={{ borderColor: emotionColor }}>
        <div className="emotion-hud-header">
          <span className="hud-title">GEOMETRIC EMOTION ENGINE</span>
          <span className="hud-badge" style={{ backgroundColor: emotionColor + '33', color: emotionColor, borderColor: emotionColor }}>
            {currentEmotion.toUpperCase()} {confidence > 0 ? `${confidence}%` : ''}
          </span>
        </div>
        <div className="hud-details">
          <span className="hud-geometry">📐 Blobs &amp; Cylinders: <strong style={{ color: '#50fa7b' }}>TRACKING</strong></span>
          {escalationStage > 0 && (
            <span className="hud-stage">Escalation: Stage {escalationStage}/4</span>
          )}
        </div>
        {Boolean(activeAction) && (
          <div className="hud-action-banner">
            ⚡ Iris: &ldquo;{typeof activeAction === 'object' && activeAction !== null ? activeAction.message : String(activeAction)}&rdquo;
          </div>
        )}
        <div className="hud-sim-buttons">
          <button
            type="button"
            className="hud-sim-btn sad"
            disabled={isSimulating}
            onClick={() => handleSimulate('sad')}
            title="Simulate Sad expression: 4-stage escalations in 3-4s intervals"
          >
            😢 Test Sad (Escalation)
          </button>
          <button
            type="button"
            className="hud-sim-btn joy"
            disabled={isSimulating}
            onClick={() => handleSimulate('joy')}
          >
            😊 Test Joy
          </button>
          <button
            type="button"
            className="hud-sim-btn neutral"
            disabled={isSimulating}
            onClick={() => handleSimulate('neutral')}
          >
            😐 Neutral
          </button>
        </div>
      </div>

      {/* Biometric Security & Profile Enrollment HUD */}
      <div className="vision-biometric-hud">
        <div className="biometric-hud-header">
          <span className="hud-title">BIOMETRIC SECURITY GATE</span>
          <span className={`hud-badge biometric-status-${hudState?.is_enrolled ? (hudState?.is_owner ? 'verified' : 'stranger') : 'none'}`}>
            {hudState?.is_enrolled 
              ? (hudState?.is_owner ? '✓ OWNER: COMMANDER' : '⚠️ STRANGER (LOCKED)')
              : '○ NOT REGISTERED'}
          </span>
        </div>
        <div className="biometric-hud-details">
          <span>Similarity: <strong>{hudState?.owner_similarity !== undefined && hudState?.owner_similarity !== null ? `${Math.round(hudState.owner_similarity * 100)}%` : 'N/A'}</strong></span>
          <span>Security: <strong>{hudState?.is_enrolled ? 'Single-Owner Lock' : 'Open Registration'}</strong></span>
        </div>
        {biometricStatus && (
          <div className="biometric-status-banner">
            {biometricStatus}
          </div>
        )}
        <div className="biometric-actions">
          <button
            type="button"
            className="biometric-btn register"
            disabled={isEnrolling}
            onClick={handleRegisterNew}
            title="Scan your face right now and register freshly as Commander"
          >
            {isEnrolling ? '⏳ Registering...' : '👤 Register My Face'}
          </button>
          <button
            type="button"
            className="biometric-btn reset"
            onClick={handleResetFace}
            title="Remove previous enrolled face and wipe stored profile"
          >
            🔄 Reset Face
          </button>
        </div>
      </div>

      <div className="vision-actions">
        <button type="button" onClick={() => onCommand('look at me')}>📷 Look at me</button>
        <button type="button" onClick={() => onCommand('what do you see on my screen')}>🖥 See my screen</button>
        <button type="button" onClick={() => onCommand('read the text on my screen')}>📝 Read the screen</button>
        <button type="button" onClick={() => onCommand('how many faces do you see')}>👤 Count faces</button>
      </div>

      <div className="vision-log">
        <div className="vision-log-title">Recent captures</div>
        {error && <div className="vision-error">{error}</div>}
        {!error && events.length === 0 && (
          <div className="vision-hint">Ask Iris to look at something — captures will appear here.</div>
        )}
        {events.map((e, i) => (
          <div key={i} className="vision-event">
            <div className="vision-event-top">
              <span className={`vision-kind kind-${e.kind}`}>
                {KIND_LABELS[e.kind] || e.kind}
              </span>
              <span className="vision-time">{timeAgo(e.time_ago)}</span>
            </div>
            {e.url && <img src={e.url} alt="capture" className="vision-thumb" />}
            <div className="vision-desc">{e.description}</div>
          </div>
        ))}
      </div>
    </aside>
  )
}