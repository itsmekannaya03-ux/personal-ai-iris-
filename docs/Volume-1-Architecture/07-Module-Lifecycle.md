# Module Lifecycle

## Purpose
Define the lifecycle management of all IRIS modules, including registration, initialization, operation, shutdown, and recovery.

## Responsibilities
- Standardize module registration and initialization
- Define lifecycle hooks and their contracts
- Manage module dependencies and startup ordering
- Handle graceful and forced shutdown

## Design Goals
- **Uniform**: Every module follows the same lifecycle
- **Hooked**: Lifecycle events are extensible
- **Safe**: Errors in one module do not affect others
- **Traceable**: Lifecycle events are logged and observable

## Architecture
```
States: REGISTERED → INITIALIZING → READY → ACTIVE → SUSPENDED → SHUTDOWN
                                   └──→ FAILED ──→ SHUTDOWN
```

## Components

### Lifecycle States
| State | Description |
|-------|-------------|
| REGISTERED | Module is known but not started |
| INITIALIZING | Module is starting resources |
| READY | Module is initialized and awaiting work |
| ACTIVE | Module is processing |
| SUSPENDED | Module is paused (e.g., resource pressure) |
| FAILED | Module encountered unrecoverable error |
| SHUTDOWN | Module has released all resources |

### Lifecycle Hooks
- `on_register()` - Module registered with Core Matrix
- `on_init(config)` - Module initializes resources
- `on_ready()` - Module signals readiness
- `on_activate()` - Module begins processing
- `on_suspend()` - Module pauses (resource pressure)
- `on_resume()` - Module resumes from suspension
- `on_shutdown()` - Module releases resources
- `on_error(error)` - Module error handler

## Data Flow
Core Matrix → Lifecycle Manager → Module Hooks → State Transition → Event Broadcast

## Public Interfaces
- `Module.get_state() -> State`
- `Module.get_health() -> HealthStatus`
- `Module.get_metrics() -> Metrics`
- `LifecycleManager.start_module(id) -> bool`
- `LifecycleManager.stop_module(id) -> bool`
- `LifecycleManager.restart_module(id) -> bool`

## Configuration
- Module config: `~/.iris/modules/<module_id>/config.yaml`
- Lifecycle policies: auto_restart, max_restarts, suspend_threshold
- Dependency declarations: `depends_on: [module_id, ...]`

## Dependencies
- Core Matrix (module registration)
- Event Dispatcher (lifecycle event broadcasting)
- Health Monitor (state monitoring)

## Security Considerations
- Module isolation prevents state corruption
- Failed modules cannot affect other module state
- Resource limits prevent runaway modules

## Failure Recovery
- Module failure → auto-restart (up to `max_restarts` times)
- Dependency failure → dependent modules suspended
- Repeated failure → module disabled, alert generated

## Future Improvements
- Phase 2: Hot-reload for module code updates
- Phase 3: Module versioning and migration

## Engineering Notes
Every module must implement all lifecycle hooks, even if as no-ops.

## Acceptance Criteria
- All modules follow the same state machine
- State transitions are logged and observable
- Module failure does not cascade
- Graceful shutdown completes within configured timeout

## References
- Volume-1-Architecture/03-Core-Matrix.md
- Volume-1-Architecture/06-Boot-Sequence.md
