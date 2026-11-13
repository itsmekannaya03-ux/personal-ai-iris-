# Communication Flow

## Purpose
Define all internal communication protocols, message formats, and data flow patterns between IRIS components.

## Responsibilities
- Document all communication pathways
- Define message formats and schemas
- Specify serialization and transport protocols
- Establish error handling and retry patterns

## Design Goals
- **Typed**: All messages have defined schemas
- **Async**: Non-blocking communication by default
- **Reliable**: Messages are delivered or explicitly fail
- **Observable**: All communication is traceable

## Architecture
```
Component A → Message Bus → Component B
         ↓                      ↓
    Event Log              Event Log
```

## Components

### Communication Patterns
- **Request/Response**: Synchronous, caller waits for response
- **Pub/Sub**: Asynchronous, one-to-many event broadcast
- **Command**: One-way, fire-and-forget instruction
- **Stream**: Continuous data flow (e.g., inference streaming)
- **Broadcast**: System-wide event (e.g., shutdown)

### Message Format
```json
{
  "id": "msg_abc123",
  "type": "request|response|event|command",
  "source": "module_id",
  "target": "module_id|*",
  "timestamp": "2026-01-01T00:00:00Z",
  "body": {},
  "correlation_id": "optional",
  "ttl": 30000
}
```

### Transport
- **In-process**: Python asyncio queues (default)
- **IPC**: Named pipes or Unix sockets (future)
- **Network**: HTTP/REST for inter-service (already defined)

## Data Flow
### User Input Flow
1. User sends message to engine (port 5743)
2. Engine routes to Neural Core
3. Neural Core sends AnalysisRequest to PIE
4. PIE returns PrivacyClassification
5. Neural Core sends ContextRequest to Memory System
6. Memory returns ContextResponse
7. Neural Core sends PersonalityRequest to Personality Engine
8. Personality returns ToneConfig
9. Neural Core assembles prompt and sends to InferenceRequest
10. Inference Engine streams/generates response
11. Neural Core sends StoreRequest to Memory System
12. Neural Core returns response to user

## Public Interfaces
- Message schema library: `app/core/messages.py`
- Bus interface: `MessageBus.publish(message)`, `MessageBus.subscribe(event, handler)`
- Request/Response: `bus.request(target, message, timeout) -> Response`

## Configuration
- Message timeout defaults: 30s (request/response), 60s (inference stream)
- Max message size: 1MB
- Retry policy: 3 retries with exponential backoff

## Dependencies
- Pydantic for message schema validation
- asyncio for async communication
- JSON for serialization (protocol buffers in future)

## Security Considerations
- Inter-module messages are not encrypted (in-process)
- Cross-process messages use TLS (future)
- Message bus validates source module identity
- Malformed messages are rejected with error

## Failure Recovery
- Timeout → retry with exponential backoff
- Malformed message → log warning, drop message
- Bus full → backpressure to sender
- Module unreachable → return ServiceUnavailable error

## Future Improvements
- Phase 2: Structured logging for all messages (ELK stack)
- Phase 3: Protobuf for performance
- Phase 4: Distributed message bus for multi-machine deployment

## Engineering Notes
All inter-module communication MUST go through the message bus. Direct calls between modules are forbidden.

## Acceptance Criteria
- Every message has a unique ID and traceable path
- Timeouts result in deterministic error responses
- Pub/sub messages reach all subscribers
- Messages are logged with correlation IDs for debugging

## References
- Volume-1-Architecture/03-Core-Matrix.md
- Volume-4-Infrastructure/06-Logging.md
- Volume-4-Infrastructure/07-Monitoring.md
