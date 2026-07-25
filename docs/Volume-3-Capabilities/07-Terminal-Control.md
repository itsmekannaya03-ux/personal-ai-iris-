# Terminal Control

## Purpose
Define the Terminal Control capability — the ability for IGRIS to execute terminal commands, interpret output, and manage system processes on behalf of the user.

## Responsibilities
- Execute terminal commands safely
- Parse and interpret command output
- Manage system processes
- Provide command suggestions
- Validate commands before execution

## Design Goals
- **Safe**: Dangerous commands require confirmation
- **Observable**: User sees command before and after execution
- **Smart**: Commands are optimized and explained
- **Recoverable**: Failed commands have clear error handling

## Architecture
```
User Request → Terminal Skill → Command Builder → Validator → Executor → Output Parser → Result
                                                    │
                                                    ▼
                                            Danger Filter
```

## Components
- **Command Builder**: Constructs terminal commands from natural language
- **Command Validator**: Checks for dangerous commands
- **Danger Filter**: Blocks known dangerous patterns
- **Command Executor**: Executes commands via subprocess
- **Output Parser**: Parses and summarizes command output
- **Process Manager**: Monitors and manages processes

## Data Flow
Natural Language → Command Builder → Validator → Danger Filter → Executor → Output → Parser → Result

## Public Interfaces
- `POST /terminal/execute` → Execute command
- `POST /terminal/suggest` → Suggest command for task
- `POST /terminal/explain` → Explain what a command does
- `POST /terminal/cancel` → Cancel running command
- `GET /terminal/processes` → List running processes

## Configuration
- Terminal enabled: `terminal_enabled` (default: false)
- Danger filter: `terminal_danger_filter` (default: strict)
- Command timeout: `command_timeout_seconds` (default: 60)
- Allowed commands: `terminal_allowed_commands` (default: all)
- Working directory: `terminal_working_dir` (default: home)

### Danger Patterns
Commands that always require confirmation:
- `rm -rf`, `format`, `dd`, `mkfs`, `fdisk`
- `sudo`, `su` (unless configured)
- Package manager install/remove
- System configuration changes

## Dependencies
- Python subprocess module
- Platform-specific: PowerShell (Windows), bash (Linux/macOS)

## Security Considerations
- Terminal control is opt-in (disabled by default)
- Dangerous commands require explicit user confirmation
- Commands are logged for audit
- User can set allowed commands whitelist
- Long-running commands have configurable timeout
- Command output may contain sensitive data — handle with care

## Failure Recovery
- Command timeout → kill process → return partial output
- Invalid command → suggest correction
- Permission denied → clear error with alternatives
- Shell crash → log and restart shell

## Future Improvements
- Phase 2: Natural language to complex command pipelines
- Phase 3: Cross-platform command translation
- Phase 4: Command execution with visual feedback

## Engineering Notes
Terminal control is extremely powerful and dangerous. Default to safe mode and require explicit user opt-in.

## Acceptance Criteria
- Commands execute and return output
- Dangerous commands are blocked without confirmation
- User can cancel running commands
- Command timeout works correctly
- Command output is parsed into structured results

## References
- Volume-5-Security/04-Permissions.md
- Volume-5-Security/06-Threat-Model.md
