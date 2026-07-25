# Planning Engine

## Purpose
Define the Planning Engine — the module that decomposes complex user requests into actionable steps, executes them in order, and manages task state across multi-turn interactions.

## Responsibilities
- Decompose complex tasks into sub-tasks
- Order and schedule sub-task execution
- Track task progress across conversation turns
- Handle dependencies between sub-tasks
- Adapt plans when tasks fail or context changes

## Design Goals
- **Decomposable**: Breaks complex tasks into atomic steps
- **Executable**: Each step can be run independently
- **Resumable**: Plans persist across conversation turns
- **Adaptable**: Plans can be modified mid-execution

## Architecture
```
Complex Request
    │
    ▼
┌────────────────────┐
│  Task Decomposer    │
│  (LLM + templates)  │
└────────┬───────────┘
         │ Steps: [{id, action, params, deps}]
         ▼
┌────────────────────┐
│  Plan Scheduler     │
│  (topological sort) │
└────────┬───────────┘
         │ Ordered steps
         ▼
┌────────────────────┐
│  Step Executor      │
│  (run + monitor)    │
└────────┬───────────┘
         │ Result per step
         ▼
┌────────────────────┐
│  State Manager      │
│  (progress + state) │
└────────────────────┘
```

## Components
- **Task Decomposer**: Uses LLM to break requests into steps
- **Plan Scheduler**: Orders steps by dependencies (topological sort)
- **Step Executor**: Runs each step, handles retry and failure
- **State Manager**: Tracks plan state across turns
- **Plan Repository**: Stores active and completed plans

## Data Flow
User Request → Decomposer → Steps → Scheduler → Ordered Steps → Executor → Results → State Manager → User

## Public Interfaces
- `POST /plan/create` → Create plan from request
- `GET /plan/status` → Get active plan status
- `POST /plan/step` → Execute next step
- `POST /plan/cancel` → Cancel active plan
- `POST /plan/update` → Modify plan mid-execution

## Configuration
- Max plan steps: `max_steps` (default: 10)
- Step timeout: `step_timeout_seconds` (default: 120)
- Max concurrent plans: `max_concurrent` (default: 3)
- Plan persistence: `plan_persistence` (default: true)

## Dependencies
- LLM (task decomposition)
- Skills System (step execution)
- Memory System (plan state persistence)

## Security Considerations
- Plans are scoped to user session
- Plan state is isolated between users
- Step execution respects permission model

## Failure Recovery
- Step failure → retry (3 attempts) → skip → mark plan as partial
- Plan timeout → save partial progress → notify user
- State corruption → invalidate plan → notify user

## Future Improvements
- Phase 2: Parallel step execution
- Phase 3: Learning from past plan patterns
- Phase 4: Automatic replanning on context change

## Engineering Notes
Plan decomposition quality depends heavily on prompt engineering. Iterate on prompts before changing code.

## Acceptance Criteria
- Complex requests are decomposed into correct steps
- Steps execute in dependency order
- Plans survive conversation interruptions
- Failed steps produce helpful error messages
- Plans can be cancelled mid-execution

## References
- Volume-2-Intelligence/08-Decision-Making.md
- Volume-3-Capabilities/01-Skill-System.md
- Volume-1-Architecture/04-AI-Orchestrator.md
