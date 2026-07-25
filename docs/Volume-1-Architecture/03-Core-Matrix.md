# Core Matrix

## Purpose
Define the Core Matrix - the runtime orchestration layer that manages module lifecycle, inter-module communication, and resource allocation within IGRIS.

## Responsibilities
- Register and initialize all system modules
- Manage module lifecycle (start, stop, restart)
- Provide inter-module communication bus
- Monitor module health and resource usage
- Coordinate shutdown and restart sequences

## Design Goals
- **Zero-dependency startup**: Modules can start in any order
- **Live reload**: Modules can be updated without system restart
- **Resource bounded**: Each module has configurable resource limits
- **Health monitored**: Modules expose health checks

## Architecture
```
Core Matrix
├── Module Registry
├── Communication Bus
├── Health Monitor
├── Resource Manager
├── Lifecycle Manager
└── Event Dispatcher
```

## Components
- **Module Registry**: Tracks all registered modules with metadata
- **Communication Bus**: Pub/sub message passing between modules
- **Health Monitor**: Periodic health checks with timeout
- **Resource Manager**: CPU/memory allocation per module
- **Lifecycle Manager**: Start, stop, restart, suspend operations
- **Event Dispatcher**: System-wide event broadcasting

## Data Flow
Module → Register → Ready → Health Check (periodic) → Message Bus → Module

## Public Interfaces
- `register_module(module: Module) -> bool`
- `send_message(target: str, message: Message) -> bool`
- `subscribe(event: str, handler: Callable) -> Subscription`
- `get_module_status(module_id: str) -> ModuleStatus`
- `restart_module(module_id: str) -> bool`

## Configuration
- Module registry path: `~/.igris/modules/`
- Resource limits per module in `~/.igris/config.yaml`
- Health check intervals: default 30s

## Dependencies
- Python 3.11+ asyncio
- Module implementations (PIE, Runtime, Skills, etc.)

## Security Considerations
- Module isolation prevents one module from crashing another
- Communication bus validates message schemas
- Resource limits prevent runaway modules

## Failure Recovery
- Dead module is auto-restarted (max 3 times)
- Unresponsive module is suspended
- Communication bus can route around failed modules

## Future Improvements
- Phase 2: WebAssembly module support
- Phase 3: Distributed module execution across network

## Engineering Notes
The Core Matrix is inspired by OS process management. Think of modules as processes.

## Acceptance Criteria
- Modules can be added at runtime without system restart
- A single module crash does not affect other modules
- Health check failures trigger configured recovery actions
- Resource limits prevent any module from starving the system

## References
- Volume-1-Architecture/07-Module-Lifecycle.md
- Volume-1-Architecture/05-Runtime.md
