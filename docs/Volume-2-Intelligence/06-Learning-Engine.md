# Learning Engine

## Purpose
Define the Learning Engine — the module that enables IGRIS to learn from user interactions, feedback, and corrections to improve over time without manual retraining.

## Responsibilities
- Record user corrections and feedback
- Identify patterns in user preferences
- Update model routing preferences based on feedback
- Manage whitelist/blacklist for privacy routing
- Provide learning statistics and insights

## Design Goals
- **Continuous**: Learns incrementally from every interaction
- **Reversible**: All learned patterns can be undone
- **Local**: Learning data never leaves the user's machine
- **Transparent**: Users can see what IGRIS has learned

## Architecture
```
User Interaction → Feedback → Learning Engine
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                              ▼
            Pattern Learner               Preference Learner
                    │                              │
                    ▼                              ▼
            Pattern Store                 Preference Store
                    │                              │
                    └──────────────┬──────────────┘
                                   ▼
                           Behavior Update
                                   │
                                   ▼
                      Intelligence Modules
```

## Components
- **Feedback Collector**: Ingests corrections, ratings, and implicit signals
- **Pattern Learner**: Identifies recurring patterns in user behavior
- **Preference Learner**: Learns user preferences (model choice, tone, etc.)
- **Privacy Learner**: Part of PIE — auto-whitelist after 3 corrections
- **Learning Store**: Persistent storage for learned patterns
- **Stats Reporter**: Provides learning statistics

## Data Flow
User feedback → Collector → Learner → Pattern/Preference Store → Module Configuration Update

## Public Interfaces
- `GET /learning/patterns` → Identified behavior patterns
- `GET /learning/preferences` → Learned preferences
- `POST /learning/forget` → Forget specific pattern
- `POST /learning/reset` → Reset all learning

## Configuration
- Learning mode: `active` | `passive` | `disabled`
- Feedback retention: `retention_days` (default: 365)
- Auto-whitelist threshold: `whitelist_threshold` (default: 3 corrections)
- Max learned patterns: `max_patterns` (default: 100)

## Dependencies
- Privacy Learner (in PIE)
- Pattern Store (persistent)
- Observation System (input signals)

## Security Considerations
- Learning data is stored locally only
- Users can view and delete all learned data
- Learning can be disabled entirely
- Learned patterns are not shared

## Failure Recovery
- Corrupted learning data → reset to defaults
- Collector failure → skip feedback for that interaction
- Store write failure → log warning, continue with in-memory only

## Future Improvements
- Phase 2: Reinforcement learning from user feedback
- Phase 3: Cross-session pattern transfer
- Phase 4: Federated learning across instances

## Engineering Notes
Learning should not introduce any latency to user interaction. Feedback collection is async.

## Acceptance Criteria
- PIE auto-whitelist activates after 3 corrections
- Learned preferences persist across restarts
- Users can view and delete specific learned items
- Learning can be completely disabled at runtime

## References
- Volume-2-Intelligence/01-Privacy-Intelligence-Engine.md
- Volume-2-Intelligence/02-Observation-System.md
- app/pie/learner.py
