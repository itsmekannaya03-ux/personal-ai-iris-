import React, { useState, useRef, useEffect, useCallback } from 'react'
import { getPresenceHudState } from '../api'

const normalize = (s) => (s || '').toLowerCase().replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim()

// Filter single filler words and noise syllables
const JUNK_NOISE_RE = /^(?:or|and|uh|um|ah|er|eh|oh|hmm|the|a|an|so|but)\b[.\s]*$/i

// Known valid solitary words (so "stop", "open", "help", "time", "hi", etc. are allowed)
const VALID_SINGLE_WORDS = new Set([
  'hi', 'hello', 'hlo', 'hey', 'yes', 'no', 'yeah', 'yep', 'nope',
  'stop', 'help', 'time', 'date', 'mute', 'unmute', 'open', 'close',
  'scan', 'status', 'restart', 'exit', 'quit', 'thanks', 'thank you',
  'clear', 'cancel', 'continue', 'more', 'wait', 'pause',
  'go', 'do', 'up', 'run', 'play', 'send', 'type', 'write',
  'haan', 'ha', 'nahi', 'karo', 'bolo', 'sunao', 'gana', 'chat'
])

function isMeaningfulSpeech(str) {
  const s = (str || '').trim()
  if (!s || s.length < 2) return false

  // If the entire utterance is just a filler word like "or", "and", "uh", discard it
  if (JUNK_NOISE_RE.test(s)) return false

  const words = s.split(/\s+/).filter(Boolean)
  if (words.length === 1) {
    const cleanWord = words[0].toLowerCase().replace(/[^a-z0-9]/g, '')
    if (cleanWord.length < 2) return false
    if (JUNK_NOISE_RE.test(cleanWord)) return false
    if (cleanWord.length < 3 && !VALID_SINGLE_WORDS.has(cleanWord)) return false
  }
  return true
}

// Acoustic Echo Canceller: checks whether speech is an echo of Iris speaking through speakers
function isEcho(text, assistantText, isSpeakingNow = false) {
  if (!isSpeakingNow) return false
  const t = normalize(text)
  if (!t) return false
  const a = normalize(assistantText)
  if (!a) return false

  // Known single valid commands (e.g. user answering "yes" or saying "stop") are never echo
  if (VALID_SINGLE_WORDS.has(t)) return false

  // Direct substring check
  if (a.includes(t) && t.length >= 3) return true
  if (t.includes(a) && a.length >= 5) return true

  // Word token overlap check
  const tWords = t.split(' ').filter(w => w.length >= 2)
  const aWords = new Set(a.split(' ').filter(w => w.length >= 2))
  if (tWords.length === 0 || aWords.size === 0) return false

  let matched = 0
  for (const w of tWords) {
    if (aWords.has(w)) matched++
  }

  return (matched / tWords.length) >= 0.5
}

const WAKE_RE = /^(?:hey|hello|hi|ok|okay|dear)?\s*(?:iris|iris|jarvis|friday|computer|assistant)\b[,\s.!?]*\s*(.*)$/i

export default function ChatInput({
  onSend,
  disabled,
  status,
  lastAssistantText = '',
  isSpeaking = false,
  onStopVoice,
  onHearingChange,
}) {
  const [text, setText] = useState('')
  const [isHearing, setIsHearing] = useState(false)
  const [convOn, setConvOn] = useState(true) // Always-ON by default
  const [wakeWord, setWakeWord] = useState(false) // Free-talk continuous listening by default
  const [sttSupported, setSttSupported] = useState(false)

  const textareaRef = useRef(null)
  const recognitionRef = useRef(null)
  const recActiveRef = useRef(false)
  const convOnRef = useRef(true)
  const wakeWordRef = useRef(false)
  const speakingRef = useRef(false)
  const disabledRef = useRef(disabled)
  const ignoreAudioRef = useRef(false)
  const onSendRef = useRef(onSend)
  const onStopVoiceRef = useRef(onStopVoice)
  const onHearingChangeRef = useRef(onHearingChange)
  const lastSendTimeRef = useRef(0)
  const lastSentTextRef = useRef('')
  const lastAssistantRef = useRef('')
  const silenceTimerRef = useRef(null)
  const currentTranscriptRef = useRef('')
  const isUserTypingRef = useRef(false)
  const isLipsMovingRef = useRef(false)
  const isSneezeRef = useRef(false)
  const isYawnRef = useRef(false)

  // Multimodal Vision-Speech Fusion: continuous lip dynamics polling
  useEffect(() => {
    let alive = true
    const pollPresence = async () => {
      try {
        const hud = await getPresenceHudState()
        if (!alive || !hud) return
        isLipsMovingRef.current = Boolean(hud.is_lips_moving)
        isSneezeRef.current = Boolean(hud.is_sneeze)
        isYawnRef.current = Boolean(hud.is_yawn)
      } catch {}
    }
    const t = setInterval(pollPresence, 1200)
    return () => { alive = false; clearInterval(t) }
  }, [])

  useEffect(() => { lastAssistantRef.current = lastAssistantText }, [lastAssistantText])
  useEffect(() => { disabledRef.current = disabled }, [disabled])
  useEffect(() => { onSendRef.current = onSend }, [onSend])
  useEffect(() => { onStopVoiceRef.current = onStopVoice }, [onStopVoice])
  useEffect(() => { onHearingChangeRef.current = onHearingChange }, [onHearingChange])
  useEffect(() => { wakeWordRef.current = wakeWord }, [wakeWord])
  useEffect(() => { convOnRef.current = convOn }, [convOn])

  // Stop assistant voice playback immediately
  const stopAssistantVoice = useCallback(() => {
    if (speakingRef.current || isSpeaking) {
      if (onStopVoiceRef.current) {
        onStopVoiceRef.current()
      }
      speakingRef.current = false
    }
  }, [isSpeaking])

  // Safe helper to notify parent when hearing state changes
  const updateHearing = useCallback((val) => {
    setIsHearing(val)
    if (onHearingChangeRef.current) {
      onHearingChangeRef.current(val)
    }
    // When user speaks, assistant output voice must turn OFF immediately!
    if (val && (speakingRef.current || isSpeaking)) {
      stopAssistantVoice()
    }
  }, [isSpeaking, stopAssistantVoice])

  // React immediately to App-level speaking prop:
  // When Iris speaks -> Input mic MUST be turned OFF completely!
  useEffect(() => {
    if (isSpeaking) {
      speakingRef.current = true
      ignoreAudioRef.current = true
      try {
        if (recognitionRef.current) {
          recognitionRef.current.abort()
        }
      } catch {}
      recActiveRef.current = false
      updateHearing(false)
      currentTranscriptRef.current = ''
      if (!isUserTypingRef.current) {
        setText('')
      }
    } else {
      speakingRef.current = false
      // Iris stopped speaking; allow audio again after quick room reverberation decay (200ms)
      const timer = setTimeout(() => {
        if (!speakingRef.current && !disabledRef.current) {
          ignoreAudioRef.current = false
          if (convOnRef.current && !recActiveRef.current) {
            safeStart()
          }
        }
      }, 200)
      return () => clearTimeout(timer)
    }
  }, [isSpeaking, updateHearing])

  // Cleanly dispatch a finished sentence
  const commitAndSendUtterance = useCallback((rawTranscript) => {
    // Cut off assistant voice immediately
    stopAssistantVoice()

    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }

    const transcript = (rawTranscript || currentTranscriptRef.current || '').trim()
    currentTranscriptRef.current = ''
    updateHearing(false)
    setText('')

    if (!transcript) return
    if (ignoreAudioRef.current || speakingRef.current || isSpeaking || disabledRef.current) return

    let target = transcript
    if (wakeWordRef.current) {
      const m = target.match(WAKE_RE)
      if (!m) {
        return // Wake-word required, no match
      }
      target = (m[1] || '').trim()
    } else {
      // Free-talk: optionally strip wake word prefix if user happened to use it
      const m = target.match(WAKE_RE)
      if (m && m[1] && m[1].trim().length >= 2) {
        target = m[1].trim()
      }
    }

    // Filter out phantom noise, single filler syllables ("or", "and", "uh")
    if (!isMeaningfulSpeech(target)) return

    // CANCEL ACOUSTIC ECHO: Only if actively speaking
    const activelySpeaking = Boolean(isSpeaking || speakingRef.current || ignoreAudioRef.current)
    if (isEcho(target, lastAssistantRef.current, activelySpeaking)) {
      console.warn('[Acoustic Echo Cancelled]:', target)
      return
    }

    // Prevent immediate duplicate submission (cancel repeating echo of user's own speech)
    const n = normalize(target)
    if (n && n === lastSentTextRef.current && (Date.now() - lastSendTimeRef.current < 4000)) {
      console.warn('[Duplicate User Echo Cancelled]:', target)
      return
    }

    lastSentTextRef.current = n
    lastSendTimeRef.current = Date.now()

    // Immediately stop & abort microphone listening so it doesn't hear Iris start speaking
    ignoreAudioRef.current = true
    try {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
    } catch {}
    recActiveRef.current = false

    // Dispatch to queued sender with isVoice=true
    onSendRef.current(target, true)
  }, [stopAssistantVoice, updateHearing, isSpeaking])

  // Safely start recognition without UI disruptions
  const safeStart = useCallback(() => {
    if (!convOnRef.current) return
    if (recActiveRef.current) return
    if (speakingRef.current || isSpeaking || ignoreAudioRef.current) return // Strict rule: Input mic is OFF while Iris speaks or in acoustic decay!
    if (disabledRef.current) return

    try {
      if (recognitionRef.current) {
        recognitionRef.current.start()
        recActiveRef.current = true
      }
    } catch (err) {
      // If recognition is already started or in transitioning state, keep active
      if (err.name === 'InvalidStateError') {
        recActiveRef.current = true
      } else {
        recActiveRef.current = false
      }
    }
  }, [isSpeaking])

  // Safely stop recognition
  const safeStop = useCallback(() => {
    try {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
    } catch { /* noop */ }
    recActiveRef.current = false
    updateHearing(false)
  }, [updateHearing])

  // Initialize SpeechRecognition
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return

    const rec = new SR()
    rec.continuous = true
    rec.interimResults = true
    rec.lang = (navigator.language && navigator.language.startsWith('en')) ? 'en-IN' : (navigator.language || 'en-IN')

    rec.onstart = () => {
      recActiveRef.current = true
    }

    rec.onresult = (e) => {
      // 1. STRICT HALF-DUPLEX: If assistant is actively speaking or disabled, discard
      // Note: Textarea focus must NEVER abort speech recognition. Only actively typing user text should pause speech.
      if (isSpeaking || speakingRef.current || ignoreAudioRef.current || disabledRef.current || (isUserTypingRef.current && text.trim().length > 0)) {
        currentTranscriptRef.current = ''
        updateHearing(false)
        return
      }

      let assembled = ''
      for (let i = 0; i < e.results.length; i++) {
        assembled += e.results[i][0].transcript + ' '
      }
      assembled = assembled.trim()

      if (!assembled) return

      // 2. ACOUSTIC ECHO GATING: If mic picked up assistant text while speakers were actively playing, drop it
      const activelySpeaking = Boolean(isSpeaking || speakingRef.current || ignoreAudioRef.current)
      if (isEcho(assembled, lastAssistantRef.current, activelySpeaking)) {
        console.warn('[Acoustic Echo Dropped in OnResult]:', assembled)
        currentTranscriptRef.current = ''
        updateHearing(false)
        return
      }

      // 2.5 Reflex impulse filter (sneeze/yawn)
      if (isSneezeRef.current || isYawnRef.current) {
        console.warn('[Microphone discarded reflex sound: sneeze or yawn]')
        currentTranscriptRef.current = ''
        return
      }

      // 3. Authenticated user speech: only now stop assistant voice playback
      stopAssistantVoice()

      currentTranscriptRef.current = assembled
      updateHearing(true)

      // Live transcript feedback in textarea
      setText(assembled)
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
        textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + 'px'
      }

      // Sentence Completion Timer:
      // Reset timer on every new speech fragment heard.
      // 1.3s pause ensures natural conversational end-of-turn detection without cutting user off
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current)
      }

      const pauseDuration = isLipsMovingRef.current ? 1800 : (wakeWordRef.current ? 1000 : 1300)
      silenceTimerRef.current = setTimeout(() => {
        commitAndSendUtterance(assembled)
      }, pauseDuration)
    }

    rec.onend = () => {
      recActiveRef.current = false

      // If speech was pending during speaking or when audio is ignored/disabled, discard it completely
      if (speakingRef.current || isSpeaking || disabledRef.current || ignoreAudioRef.current) {
        currentTranscriptRef.current = ''
        updateHearing(false)
        // Self-heal: retry starting once speaking or disabled state resolves
        setTimeout(() => {
          if (convOnRef.current && !recActiveRef.current && !speakingRef.current && !isSpeaking && !disabledRef.current && !ignoreAudioRef.current) {
            safeStart()
          }
        }, 300)
        return
      }

      // Multimodal Lip Continuity: If lips are still visibly oscillating in camera, keep listening!
      if (isLipsMovingRef.current && convOnRef.current && !speakingRef.current && !isSpeaking && !disabledRef.current) {
        setTimeout(() => {
          if (!recActiveRef.current && convOnRef.current) {
            safeStart()
          }
        }, 50)
        return
      }

      // If speech was pending when browser silence timeout ended, commit it now
      if (currentTranscriptRef.current && currentTranscriptRef.current.length >= 2) {
        commitAndSendUtterance(currentTranscriptRef.current)
      } else {
        updateHearing(false)
      }

      // Silent self-healing reconnect: seamless background restart without UI blinking
      if (convOnRef.current && !speakingRef.current && !isSpeaking && !disabledRef.current && !ignoreAudioRef.current) {
        setTimeout(() => {
          if (convOnRef.current && !recActiveRef.current && !speakingRef.current && !isSpeaking && !disabledRef.current && !ignoreAudioRef.current) {
            safeStart()
          }
        }, 80)
      }
    }

    rec.onerror = (e) => {
      if (e.error === 'no-speech') {
        // Natural ambient silence; onend will automatically and silently restart
        return
      }
      recActiveRef.current = false
      updateHearing(false)
      if (convOnRef.current && !speakingRef.current && !isSpeaking && !disabledRef.current && !ignoreAudioRef.current) {
        setTimeout(() => {
          if (convOnRef.current && !recActiveRef.current && !speakingRef.current && !isSpeaking && !disabledRef.current && !ignoreAudioRef.current) {
            safeStart()
          }
        }, 200)
      }
    }

    recognitionRef.current = rec
    setSttSupported(true)

    // Immediate auto-start
    if (convOnRef.current && !speakingRef.current && !isSpeaking && !disabledRef.current) {
      setTimeout(safeStart, 100)
    }

    // Continuous Heartbeat Watchdog: Prevents microphone dormancy over long hours of conversation
    const watchdog = setInterval(() => {
      if (
        convOnRef.current &&
        !recActiveRef.current &&
        !speakingRef.current &&
        !isSpeaking &&
        !disabledRef.current &&
        !ignoreAudioRef.current
      ) {
        safeStart()
      }
    }, 1000)

    // Window interaction fallback for strict browser autoplay
    const unlockAudio = () => {
      if (convOnRef.current && !recActiveRef.current && !speakingRef.current && !isSpeaking && !disabledRef.current) {
        safeStart()
      }
    }
    window.addEventListener('click', unlockAudio, { passive: true })
    window.addEventListener('keydown', unlockAudio, { passive: true })
    window.addEventListener('touchstart', unlockAudio, { passive: true })

    return () => {
      clearInterval(watchdog)
      window.removeEventListener('click', unlockAudio)
      window.removeEventListener('keydown', unlockAudio)
      window.removeEventListener('touchstart', unlockAudio)
      try { rec.abort() } catch { }
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current)
    }
  }, [commitAndSendUtterance, safeStart, stopAssistantVoice, updateHearing, isSpeaking])

  // Watchdog Heartbeat: Every 1.5s, ensures the mic is active when appropriate
  useEffect(() => {
    const watchdog = setInterval(() => {
      if (convOnRef.current && !recActiveRef.current && !speakingRef.current && !isSpeaking && !disabledRef.current) {
        safeStart()
      }
    }, 1500)
    return () => clearInterval(watchdog)
  }, [safeStart, isSpeaking])

  // Monitor backend speaking status: Mute during TTS and provide post-speech echo cooldown
  useEffect(() => {
    if (!convOn) return
    let wasSpeaking = false

    const pollId = setInterval(async () => {
      try {
        const res = await fetch('/api/status')
        const data = await res.json()
        const isSpk = !!data.speaking
        speakingRef.current = isSpk

        if (isSpk) {
          wasSpeaking = true
          ignoreAudioRef.current = true
          try {
            if (recognitionRef.current && recActiveRef.current) {
              recognitionRef.current.abort()
            }
          } catch {}
          recActiveRef.current = false
          updateHearing(false)
          currentTranscriptRef.current = ''
          if (!isUserTypingRef.current) {
            setText('')
          }
        } else if (wasSpeaking) {
          wasSpeaking = false
          // Assistant finished speaking; wait 600ms for room echo to decay
          setTimeout(() => {
            if (!speakingRef.current && !disabledRef.current) {
              ignoreAudioRef.current = false
              currentTranscriptRef.current = ''
              if (convOnRef.current && !recActiveRef.current) {
                safeStart()
              }
            }
          }, 600)
        } else if (!disabledRef.current) {
          ignoreAudioRef.current = false
        }
      } catch { /* backend offline */ }
    }, 120)

    return () => clearInterval(pollId)
  }, [convOn, safeStart, updateHearing])

  const toggleMic = () => {
    if (convOn) {
      setConvOn(false)
      updateHearing(false)
      safeStop()
    } else {
      lastSendTimeRef.current = Date.now()
      setConvOn(true)
      safeStart()
    }
  }

  const handleSubmit = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    stopAssistantVoice()
    isUserTypingRef.current = false
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }
    currentTranscriptRef.current = ''
    updateHearing(false)

    // Abort mic immediately so speaker sound doesn't get captured
    ignoreAudioRef.current = true
    try {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
    } catch {}
    recActiveRef.current = false

    onSend(trimmed)
    setText('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleInput = (e) => {
    stopAssistantVoice()
    const val = e.target.value
    isUserTypingRef.current = val.length > 0
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }
    currentTranscriptRef.current = ''
    updateHearing(false)
    setText(val)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px'
  }

  const handleFocus = () => {
    if (text.trim().length > 0) {
      isUserTypingRef.current = true
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }
  }

  const handleBlur = () => {
    if (!text.trim()) {
      isUserTypingRef.current = false
    }
  }

  const placeholder = status === 'disconnected'
    ? 'Backend offline — start the server first...'
    : isSpeaking
      ? '🔇 Iris speaking (input mic OFF). Click Interrupt or type to speak...'
      : convOn
        ? isHearing
          ? '🔴 You speaking (assistant voice OFF)…'
          : wakeWord
            ? '🎤 Listening — Say "Hey Iris" + command…'
            : '🎤 Mic Live — speak anytime…'
        : 'Microphone muted — click to un-mute...'

  return (
    <div className="input-row">
      {sttSupported && (
        <>
          <button
            type="button"
            className={`wake-button ${wakeWord ? 'on' : ''}`}
            onClick={() => setWakeWord((w) => !w)}
            title={wakeWord ? 'Wake word ON — only responds after "Hey Iris"' : 'Free-talk ON — responds to any speech'}
            disabled={status === 'disconnected'}
          >
            {wakeWord ? '🔊 Hey Iris' : '🗣 Free-talk'}
          </button>
          {isSpeaking ? (
            <button
              type="button"
              className="mic-button speaking-interrupt"
              onClick={() => {
                stopAssistantVoice()
                setTimeout(() => {
                  if (convOnRef.current) safeStart()
                }, 100)
              }}
              title="Iris is speaking (Input Mic OFF). Click to interrupt Iris and speak!"
            >
              🛑 Interrupt
            </button>
          ) : (
            <button
              type="button"
              className={`mic-button ${convOn ? 'conversation' : ''} ${isHearing ? 'hearing' : ''}`}
              onClick={toggleMic}
              title={convOn ? 'Microphone Always-On (Click to mute)' : 'Microphone Muted (Click to turn on)'}
              disabled={status === 'disconnected'}
            >
              {convOn ? (isHearing ? '🔴' : '🎤') : '🔇'}
            </button>
          )}
        </>
      )}
      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleInput}
        onFocus={handleFocus}
        onBlur={handleBlur}
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
