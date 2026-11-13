# Boot Sequence

## Purpose
Define the complete system boot sequence from power-on to fully operational IRIS system.

## Responsibilities
- Document all initialization steps in order
- Define health check points at each stage
- Specify error handling for each boot stage
- Ensure consistent startup across platforms

## Design Goals
- **Fast**: Boot to ready in under 10 seconds
- **Reliable**: Every startup path is tested
- **Observable**: Boot progress is visible to user
- **Recoverable**: Failed boot attempts provide actionable error messages

## Architecture
```
Phase 1: Kernel Init (0-1s)
Phase 2: Core Matrix Init (1-3s)
Phase 3: Module Loading (3-5s)
Phase 4: Model Loading (5-8s)
Phase 5: Health Check (8-10s)
Phase 6: Ready
```

## Components

### Phase 1: Kernel Init
- Load configuration files
- Initialize logging system
- Set up signal handlers
- Create runtime directories (`~/.iris/`)

### Phase 2: Core Matrix Init
- Initialize Communication Bus
- Start Health Monitor
- Register available modules
- Initialize Event Dispatcher

### Phase 3: Module Loading
- Load PIE (Privacy Intelligence Engine)
- Load Memory System
- Load Personality Engine
- Load Skills System
- Load Voice System

### Phase 4: Model Loading
- Model Manager checks available models
- Load base model (`llama3.2:3b`)
- Warm up inference cache
- Verify model health

### Phase 5: Health Check
- Ping each module
- Verify memory backend connection (ChromaDB)
- Verify API server health
- Report boot status

### Phase 6: Ready
- Start server on port 5743
- Signal ready to CLI
- Log boot complete with timing

## Data Flow
Boot progress is streamed to CLI output and logged to `~/.iris/logs/boot.log`.

## Public Interfaces
- `GET /health` → Boot status (starting/ready/failed)
- `GET /boot/log` → Complete boot log

## Configuration
- Boot timeout per phase: `phase_timeout` in config
- Module loading order: `module_load_order` in config
- Model warm-up: `warm_up_models` list in config

## Dependencies
- All modules must be installed
- ChromaDB must be accessible
- At least one model must be available
- API server is optional (engine can run standalone)

## Security Considerations
- Boot processes run with minimum required permissions
- Configuration files validated before loading
- Failed health checks never expose internal state

## Failure Recovery
- Phase timeout → retry once → skip module → log failure
- Critical module failure → boot fails with error message and recovery instructions
- Model not found → boot succeeds with warning, user prompted to install

## Future Improvements
- Phase 2: Parallel module loading
- Phase 3: Incremental boot (start minimal, load extras on demand)
- Phase 4: Boot performance optimization with caching

## Engineering Notes
Boot sequence should be tested on each operating system (Windows, macOS, Linux).

## Acceptance Criteria
- Boot completes in under 10 seconds on modern hardware
- Missing non-critical module does not prevent boot
- Failed boot provides actionable error message
- Boot log is always persisted, even on failure

## References
- Volume-1-Architecture/07-Module-Lifecycle.md
- Volume-1-Architecture/03-Core-Matrix.md
- Volume-1-Architecture/05-Runtime.md
