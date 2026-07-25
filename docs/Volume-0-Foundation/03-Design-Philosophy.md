# Design Philosophy

## Purpose
Define the design philosophy that shapes user experience, system behavior, and interaction patterns in IGRIS.

## Responsibilities
- Guide user interface design decisions
- Shape interaction patterns and dialogue design
- Define system personality and tone
- Ensure consistent experience across all interfaces

## Design Goals
- **Invisible**: The best AI is the one you forget is there
- **Proactive**: Anticipate needs before they are expressed
- **Respectful**: Never interrupt, never waste time, never be creepy
- **Adaptive**: Learn from behavior, not from configuration

## Architecture
Design philosophy manifests across all layers: CLI, web dashboard, voice interface, and API responses.

## Components
- **5 Modes**: Normal, Assistant, Friend, Focus, Silent — each with distinct personality
- **6 Themes**: Blob, Terminal, Voicebar, Drum, Hologram, Minimal — visual identity
- **Personality Engine**: Adapts tone based on emotion detection and user relationship

## Data Flow
User interaction → Mode selection → Personality prompt → Response generation → Theme rendering

## Public Interfaces
All interfaces (CLI, web, voice, API) follow the same design philosophy with appropriate medium-specific adaptations.

## Configuration
User preferences for mode, theme, AI name, and personality are stored in profile.json.

## Dependencies
- Tailwind CSS for web theming
- pyttsx3 for TTS voice
- lucide-react for iconography

## Security Considerations
Design never asks for more information than needed. Privacy-focused design means minimal data collection.

## Failure Recovery
When errors occur, IGRIS communicates clearly and helpfully without technical jargon.

## Future Improvements
- Phase 2: Adaptive UI that changes based on usage patterns
- Phase 3: Voice personality adaptation

## Engineering Notes
Design decisions should be justified by philosophy, not personal preference.

## Acceptance Criteria
- Users can personify IGRIS (name, personality, theme)
- IGRIS adapts its tone to user emotion
- All interfaces feel like the same product

## References
- Volume-2-Intelligence/04-Personality-Engine.md
- 02-Engineering-Principles.md
