# Logging

## Purpose
Define the Logging system — the centralized logging infrastructure that captures system events, errors, and operational data for debugging, auditing, and monitoring.

## Responsibilities
- Capture structured log entries from all modules
- Manage log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Rotate and archive log files
- Provide log querying and filtering
- Sanitize sensitive data from logs
- Support multiple log outputs (file, console, remote)

## Design Goals
- **Structured**: Logs are JSON for machine parsing
- **Comprehensive**: All modules log consistently
- **Safe**: Sensitive data is never logged
- **Performant**: Logging adds < 1ms overhead
- **Searchable**: Logs can be filtered and queried efficiently

## Architecture
```
Module → Logger → Log Level Filter → Sanitizer → Output
                                                    │
                                            ┌───────┴───────┐
                                            ▼               ▼
                                       File Logger    Console Logger
                                            │
                                            ▼
                                       Log Rotator (archive)
```

## Components
- **Logger**: Per-module logger instances
- **Log Level Filter**: Filters by configured level
- **Sanitizer**: Removes PII and secrets from log entries
- **File Logger**: Writes to rotating log files
- **Console Logger**: Outputs to stdout/stderr
- **Log Rotator**: Archives old logs based on size/age
- **Query Engine**: Filters and searches logs

## Data Flow
Event → Logger → Format (JSON) → Level Check → Sanitize → Write (File + Console)

## Public Interfaces
- `GET /logs/query` → Query logs with filters
- `GET /logs/stream` → Stream live logs
- `POST /logs/level` → Set log level at runtime
- `POST /logs/export` → Export logs
- `GET /logs/status` → Logging system status

## Configuration
- Log directory: `~/.iris/logs/`
- Default log level: `INFO`
- Log format: `json` (structured)
- Max file size: `max_file_size_mb` (default: 100)
- Max files: `max_files` (default: 10)
- Sanitization patterns: configured in sanitizer rules

## Dependencies
- Python logging module
- JSON serializer
- File system (log storage)

## Security Considerations
- Sensitive data is sanitized before writing to logs
- API keys, passwords, and tokens are never logged
- User message content is excluded from logs (configurable)
- Log files have restricted file permissions
- Log exports are encrypted by default

## Failure Recovery
- Log file write failure → fallback to console logging
- Disk full → delete oldest archived logs
- Sanitizer failure → skip log entry, log the error

## Future Improvements
- Phase 2: Remote log aggregation (ELK stack)
- Phase 3: Log-based alerting
- Phase 4: Structured log analysis and pattern detection

## Engineering Notes
Good logging is essential for debugging distributed systems. Log early, log often, but never log secrets.

## Acceptance Criteria
- All modules produce structured JSON logs
- Log levels can be changed at runtime
- Log sanitization removes all known PII patterns
- Log files are rotated without data loss
- Logs can be queried by module, level, and time range

## References
- Volume-4-Infrastructure/07-Monitoring.md
- Volume-5-Security/05-Encryption.md
