# AI Orchestrator

## Purpose
Define the AI Orchestrator - the central coordinator that routes user input through the appropriate processing pipeline and manages the interaction between intelligence modules.

## Responsibilities
- Route user input to appropriate processing pipeline
- Manage intent detection and classification
- Coordinate multi-step reasoning chains
- Determine when to use local vs cloud inference
- Manage conversation context and session state

## Design Goals
- **Pipeline-based**: Processing happens in configurable pipelines
- **Context-aware**: Decisions depend on conversation history and user state
- **Efficient**: Minimize latency by parallelizing where possible
- **Adaptable**: Pipelines can be modified at runtime

## Architecture
```
Input → Intent Detection → Pipeline Selection
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            Local Pipeline          Cloud Pipeline
            (via PIE local)         (via PIE cloud)
                    │                     │
                    └──────────┬──────────┘
                               ▼
                        Response Generation
                               │
                               ▼
                            Output
```

## Components
- **Intent Detector**: Classifies input intent (question, command, casual, task)
- **Pipeline Selector**: Chooses processing pipeline based on intent, privacy, and context
- **Task Decomposer**: Breaks complex tasks into sub-tasks
- **Context Manager**: Maintains and prunes conversation context
- **Pipeline Executor**: Executes the selected pipeline

## Data Flow
1. Input received → Intent Detector classifies
2. PIE determines privacy routing
3. Pipeline Selector chooses local or cloud pipeline
4. Task Decomposer splits if needed
5. Pipeline Executor runs each pipeline step
6. Response Generator produces output

## Public Interfaces
- `process(message: str, session_id: str) -> Response`
- `process_async(message: str, session_id: str, callback: Callable) -> Task`
- `interrupt(session_id: str) -> bool`
- `get_pipeline(session_id: str) -> Pipeline`

## Configuration
- Pipeline definitions in `orchestrator/pipelines.yaml`
- Intent detection model: `llama3.2:3b` (local)
- Default pipeline: balanced (local priority with PIE cloud routing)

## Dependencies
- PIE (privacy classification)
- Inference Engine (model execution)
- Memory System (context retrieval)
- Skills System (tool execution)

## Security Considerations
- PIE ensures privacy classification before any routing decision
- Cloud pipeline only activates when PIE explicitly allows
- All pipeline decisions are logged for audit

## Failure Recovery
- Pipeline step failure triggers retry (3 attempts)
- Cloud pipeline fallback → local pipeline
- Complete pipeline failure → graceful error response

## Future Improvements
- Phase 2: Dynamic pipeline construction based on task analysis
- Phase 3: Learning-optimized pipeline selection

## Engineering Notes
The orchestrator should be stateless - all context is stored in the Context Manager.

## Acceptance Criteria
- Intent detection accuracy > 90% for defined intents
- Pipeline switching adds < 200ms overhead
- Context pruning prevents token overflow
- Orchestrator processes 100 conversations simultaneously

## References
- Volume-1-Architecture/02-Neural-Core.md
- Volume-2-Intelligence/01-Privacy-Intelligence-Engine.md
- Volume-2-Intelligence/07-Reasoning-Engine.md
