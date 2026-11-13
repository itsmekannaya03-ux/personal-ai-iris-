# Personality Engine

## Purpose
Define the Personality Engine — the module that gives IRIS its adaptive personality, voice, and emotional intelligence across 5 distinct modes.

## Responsibilities
- Adapt response tone based on selected mode
- Detect user emotion from text input
- Adjust personality weight based on user relationship
- Maintain consistent character across sessions
- Support user-configured AI name and persona

## Design Goals
- **Expressive**: Distinct personality across 5 modes
- **Adaptive**: Tone changes with user emotion and context
- **Consistent**: Same mode always produces same personality
- **Configurable**: Users can customize name, tone, and persona

## Architecture
```
User Input
    │
    ▼
Emotion Detector ──→ Personality Engine ──→ Context Builder
         │                    │                      │
         │                    ▼                      │
         │            Mode Selector                  │
         │      (Normal/Assistant/Friend/Focus/Silent)│
         │                    │                      │
         ▼                    ▼                      ▼
    Emotion Score        Tone Config              Personality Prompt
         │                    │                      │
         └────────────────────┴──────────────────────┘
                                    │
                                    ▼
                            Response Generator
```

## Components
- **Emotion Detector**: Classifies user emotion from text (happy, sad, angry, neutral, anxious, etc.)
- **Mode Manager**: Manages the 5 modes with distinct personalities
- **Tone Adapter**: Adjusts tone weight based on emotion and mode
- **Persona Store**: User-configured personality preferences
- **Prompt Builder**: Constructs personality-injected system prompts

### Mode Personalities
| Mode | Description | Tone |
|------|-------------|------|
| Normal | Balanced assistant | Professional, helpful |
| Assistant | Pure functionality | Concise, direct |
| Friend | Casual conversation | Warm, casual, personal |
| Focus | Deep work mode | Minimal, only essential |
| Silent | Passive observation | Minimal responses |

## Data Flow
1. User input → Emotion Detector
2. Emotion scores + Mode → Personality Engine
3. Tone Config + User Persona → Prompt Builder
4. Personality-injected prompt → Inference Engine
5. Response generated with appropriate tone

## Public Interfaces
- `POST /personality/mode` → Set mode
- `GET /personality/mode` → Get current mode
- `POST /personality/emotion` → Detect emotion in text
- `POST /personality/name` → Set AI name
- `GET /personality/config` → Get personality config

## Configuration
- Personality config: `~/.iris/personality.json`
- AI name: default "IRIS"
- Wake word: "hey iris"
- Mode-specific system prompts in `app/core/personality/prompts/`

## Dependencies
- Emotion detection model (via Inference Engine)
- Prompt templates (modes)
- User profile (for persona settings)

## Security Considerations
- Personality data is stored locally
- Emotion detection is never shared externally
- Modes do not affect privacy routing decisions

## Failure Recovery
- Emotion detection failure → neutral tone fallback
- Mode config corruption → reset to Normal mode
- Prompt template missing → generic prompt fallback

## Future Improvements
- Phase 2: Voice-based emotion detection
- Phase 3: Adaptive personality that evolves with user
- Phase 4: Multi-modal personality (voice + text + visual)

## Engineering Notes
Personality is implemented entirely through prompt engineering. No fine-tuning required.

## Acceptance Criteria
- Each mode produces distinctly different response styles
- Emotion detection achieves > 80% accuracy on basic emotions
- Users can change AI name and see it reflected in responses
- Mode switching takes effect on next response

## References
- Volume-0-Foundation/03-Design-Philosophy.md
- Volume-3-Capabilities/03-Voice-System.md
- Volume-1-Architecture/05-Runtime.md
