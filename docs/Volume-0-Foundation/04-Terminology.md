# Terminology

## Purpose
Define a consistent glossary of terms used throughout the IRIS system. All documentation, code, and communication should use these terms consistently.

## Responsibilities
- Maintain a single source of truth for terminology
- Resolve naming conflicts
- Onboard new team members to the IRIS vocabulary

## Design Goals
- **Precise**: Each term has exactly one meaning
- **Consistent**: Terms are used consistently across all contexts
- **Discoverable**: Easy to find definitions

## Architecture
Terms are organized by domain area. Each term includes its definition, usage context, and related terms.

## Components

### Core Concepts
| Term | Definition |
|------|-----------|
| IRIS OS | The complete Personal AI Operating System |
| IRIS Runtime | The core orchestration engine (app/runtime/) |
| PIE | Privacy Intelligence Engine, responsible for privacy classification and routing |
| Model Manager | Selects the best AI model for each task |
| Inference Engine | Abstract interface for executing AI models |

### Intelligence
| Term | Definition |
|------|-----------|
| Intent | What the user wants to accomplish |
| Emotion | The user's emotional state detected from text |
| Memory | Three-tier storage (short-term, long-term, deep) |
| Personality Engine | Adapts response tone based on mode and emotion |
| Planning Engine | Breaks down complex tasks into steps |

### Privacy
| Term | Definition |
|------|-----------|
| Privacy Level | Classification: low, medium, high, critical |
| Anonymization | Replacing PII with placeholder tokens before cloud routing |
| Privacy Profile | User-configurable privacy settings |
| Adaptive Learning | PIE improves decisions from user corrections |

### Infrastructure
| Term | Definition |
|------|-----------|
| ChromaDB | Vector database for long-term memory storage |
| Deep Memory | Encrypted permanent storage for critical memories |
| Installer Token | One-time token used during user installation |
| Clone | A user's personal AI instance with their profile |

## Data Flow
Terms are used consistently in code (variable names), documentation, API responses, and user-facing messages.

## Public Interfaces
API responses use these terms in JSON field names. CLI commands use these terms in help text.

## Configuration
Configuration files use these terms for setting names.

## Dependencies
None. This document is self-contained.

## Security Considerations
Terms related to security and privacy are defined with extra precision to avoid ambiguity.

## Failure Recovery
If a term becomes ambiguous, it should be clarified or replaced.

## Future Improvements
- Phase 2: Automated terminology checking in CI
- Phase 3: Localization glossary for internationalization

## Engineering Notes
When introducing a new term, check if an existing term already describes the concept.

## Acceptance Criteria
- No two terms have conflicting definitions
- All code, docs, and APIs use consistent terminology
- New contributors can understand the glossary in one read

## References
- All documents in this repository use this terminology
