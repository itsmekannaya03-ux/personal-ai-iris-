# Neural Core

## Purpose
Define the Neural Core - the central processing unit of IRIS that coordinates all intelligence modules, manages state, and orchestrates responses.

## Responsibilities
- Coordinate intelligence modules (PIE, Memory, Personality, Planning, Learning, Reasoning)
- Manage conversation state and context
- Orchestrate multi-step response generation
- Maintain the AI loop: Observe → Reason → Act → Learn

## Design Goals
- **Deterministic**: Given same input and state, produce same output
- **Stateful**: Maintain context across interactions
- **Extensible**: New intelligence modules plug in without modification
- **Composable**: Modules work together without knowledge of each other

## Architecture
```
User Input → Intent → Neural Core
                              ├── PIE (privacy classification)
                              ├── Memory (context retrieval)
                              ├── Personality Engine (tone adaptation)
                              ├── Planning Engine (task decomposition)
                              ├── Learning Engine (pattern extraction)
                              └── Reasoning Engine (logical inference)
                                      │
                                      ▼
                              Response Generator → Output
```

## Components
- **Intent Router**: Classifies user intent from input text
- **State Manager**: Maintains conversation state across turns
- **Module Coordinator**: Calls intelligence modules in correct order
- **Context Builder**: Assembles prompt context from all modules
- **Response Generator**: Produces final response text

## Data Flow
1. Receive user input
2. Intent Router classifies intent
3. PIE classifies privacy level
4. Memory retrieves relevant context
5. Personality Engine adapts tone
6. Planning Engine decomposes if needed
7. Learning Engine updates patterns
8. Reasoning Engine performs logical inference
9. Context Builder assembles prompt
10. Response Generator produces output

## Public Interfaces
- `process_input(user_input: str, session_id: str) -> Response`
- `get_state(session_id: str) -> SessionState`
- `reset_session(session_id: str) -> bool`

## Configuration
Configured through Neural Core config in `config.yaml`. Module selection, processing order, and timeout values.

## Dependencies
- PIE (Privacy Intelligence Engine)
- Memory System (3-tier)
- Personality Engine
- Planning Engine
- Learning Engine
- Reasoning Engine
- Decision Making Module

## Security Considerations
- Neural Core never stores raw user input in logs
- State is isolated per session
- Memory access is gated by PIE classification

## Failure Recovery
- Module timeout triggers fallback response
- Missing module skips gracefully
- State corruption triggers session reset

## Future Improvements
- Phase 2: Parallel module execution
- Phase 3: Neural Core with learned processing order

## Engineering Notes
The Neural Core is the single most important module. All other modules serve it.

## Acceptance Criteria
- Module execution order is configurable
- Missing modules do not crash the system
- Context window respects token limits even with many modules
- Response generation completes within 2x base inference time

## References
- Volume-1-Architecture/04-AI-Orchestrator.md
- Volume-2-Intelligence (all documents)
- Volume-1-Architecture/03-Core-Matrix.md
