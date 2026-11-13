# Hybrid Intelligence

## Purpose
Define the Hybrid Intelligence architecture — the system that intelligently routes inference requests between local models and cloud providers based on privacy, capability, and performance requirements.

## Responsibilities
- Determine optimal inference location (local vs cloud)
- Apply PIE privacy classification to routing decisions
- Anonymize data before cloud transmission
- Reconstruct cloud responses with original context
- Manage cloud provider credentials and selection
- Monitor latency and cost for cloud usage

## Design Goals
- **Privacy-first**: Sensitive data never leaves local machine
- **Intelligent**: Best model for each task, not cheapest or fastest
- **Transparent**: User knows when cloud is being used
- **Efficient**: Minimize latency by caching frequent results
- **Cost-aware**: Track and limit cloud API usage costs

## Architecture
```
Request → PIE Classifier → Hybrid Router
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
               Local Path          Cloud Path
                    │                   │
                    ▼                   ▼
            Local Inference       Anonymizer
                    │                   │
                    │                   ▼
                    │           Cloud Provider
                    │                   │
                    │                   ▼
                    │           De-anonymizer
                    │                   │
                    └─────────┬─────────┘
                              ▼
                        Response
```

## Components
- **Hybrid Router**: Decision engine with full routing tree
- **PIE Integration**: Privacy classification for routing context
- **Anonymization Pipeline**: Entity replacement for cloud requests
- **De-anonymization Pipeline**: Entity restoration from cloud responses
- **Provider Selector**: Chooses cloud provider based on task and cost
- **Usage Tracker**: Tracks cloud API usage and costs

## Data Flow
Request → PIE → Router → (Local: InferenceEngine) | (Cloud: Anonymizer → Provider → De-anonymizer) → Response

## Public Interfaces
- `GET /hybrid/status` → Current hybrid mode and provider
- `POST /hybrid/route` → Manually route a request
- `GET /hybrid/usage` → Cloud usage statistics
- `POST /hybrid/provider` → Set cloud provider
- `GET /hybrid/history` → Routing decision history

## Configuration
- Hybrid mode: `local_only` | `hybrid` | `cloud_preferred` | `cloud_only`
- Default mode: `hybrid`
- Cloud provider config: `~/.iris/cloud.yaml`
- Cost limits: `monthly_budget` (default: $10)
- Anonymization rules in PIE configuration

## Dependencies
- PIE (privacy classification and anonymization)
- Cloud Provider abstraction
- Runtime Inference Engine (local path)
- Credential Store (for cloud API keys)

## Security Considerations
- Cloud routing requires explicit PIE approval
- Anonymization removes all known PII patterns
- Cloud provider credentials are encrypted at rest
- Usage records do not contain request contents
- User can force local-only mode

## Failure Recovery
- Cloud provider unavailable → fallback to local inference
- Anonymization failure → route to local
- Cost limit reached → switch to local-only
- Authentication failure → clear error with credential fix steps

## Future Improvements
- Phase 2: Intelligent caching of cloud responses
- Phase 3: Cost-performance optimization algorithm
- Phase 4: Multi-provider load balancing

## Engineering Notes
Hybrid intelligence is the key differentiator from pure local or pure cloud AI assistants.

## Acceptance Criteria
- PIE classification correctly identifies sensitive content
- Anonymization removes PII from cloud requests
- De-anonymization restores original context in responses
- Cloud usage is tracked and bounded by cost limits
- Hybrid mode is switchable at runtime

## References
- Volume-2-Intelligence/01-Privacy-Intelligence-Engine.md
- Volume-4-Infrastructure/04-Cloud-Providers.md
- app/pie/router.py
