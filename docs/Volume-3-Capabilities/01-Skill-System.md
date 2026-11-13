# Skill System

## Purpose
Define the Skill System — the modular capability framework that allows IRIS to perform specific tasks through registered skill modules.

## Responsibilities
- Register and manage skill modules
- Route user intents to appropriate skills
- Execute skills with proper context
- Handle skill results and errors
- Provide skill discovery and introspection

## Design Goals
- **Modular**: Skills are independent, self-contained modules
- **Discoverable**: Users can list and learn about available skills
- **Composable**: Skills can be chained together
- **Safe**: Skills execute in sandboxed context

## Architecture
```
User Intent → Intent Router → Skill Matcher → Skill Executor → Skill Module → Response
                                                    │
                                                    ▼
                                              Skill Registry
                                              (8 built-in skills)
```

## Components
- **Skill Registry**: Central registry of all available skills
- **Skill Matcher**: Matches user intent to best skill
- **Skill Executor**: Runs skill with proper context and timeout
- **Intent Router**: Routes intents to skill system or direct LLM

### Built-in Skills
| Skill | Description | Module |
|-------|-------------|--------|
| Calendar | Schedule management | `app/core/skills/calendar.py` |
| Web Research | Web search and content fetching | `app/core/skills/web_research.py` |
| Media Control | Music, video playback control | `app/core/skills/media_control.py` |
| File Search | Local file search and indexing | `app/core/skills/file_search.py` |
| Email | Email composition and management | `app/core/skills/email.py` |
| Weather | Weather information | `app/core/skills/weather.py` |
| Notes | Note taking and retrieval | `app/core/skills/notes.py` |
| Tasks | Task and todo management | `app/core/skills/tasks.py` |

## Data Flow
1. User intent detected as skill-relevant
2. Skill Matcher selects best skill
3. Skill Executor prepares context
4. Skill module executes with parameters
5. Result returned to Neural Core for response generation

## Public Interfaces
- `GET /skills/list` → List available skills
- `GET /skills/<name>/info` → Skill details
- `POST /skills/<name>/execute` → Execute skill
- `POST /skills/register` → Register new skill

## Configuration
- Skills config: `~/.iris/skills.yaml`
- Skills enabled/disabled per user
- Skill timeout: `skill_timeout_seconds` (default: 30)
- API keys for web skills in `~/.iris/credentials/`

## Dependencies
- Intent Router (for skill matching)
- Inference Engine (skill coordination)
- Plugin System (for third-party skills)

## Security Considerations
- Skills run with minimum permissions
- Skills cannot access files outside authorized paths
- Network access requires explicit user consent
- API keys stored in encrypted credential store

## Failure Recovery
- Skill timeout → return timeout error
- Skill crash → log and disable skill
- Missing dependency → clear error message with install instructions

## Future Improvements
- Phase 2: Skill chaining (composing skills)
- Phase 3: Skill marketplace for community skills
- Phase 4: Skill auto-generation from natural language

## Engineering Notes
Skills should follow the single-responsibility principle. One skill, one capability.

## Acceptance Criteria
- All 8 built-in skills are implemented and functional
- New skills can be added without modifying core code
- Skills time out gracefully
- Users can enable/disable skills at runtime
- Skills are discoverable through CLI and API

## References
- Volume-3-Capabilities/02-Plugin-System.md
- Volume-1-Architecture/04-AI-Orchestrator.md
- app/core/skills/__init__.py
