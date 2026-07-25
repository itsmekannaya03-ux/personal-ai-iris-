# Cloud Providers

## Purpose
Define the Cloud Provider abstraction layer — the system that provides a unified interface for different cloud AI inference providers, enabling transparent switching between providers.

## Responsibilities
- Define abstract CloudProvider interface
- Implement provider-specific adapters
- Handle authentication and credential management
- Manage provider health and availability
- Normalize provider responses to unified format

## Design Goals
- **Abstract**: One interface for all providers
- **Pluggable**: Add new providers without code changes
- **Resilient**: Failover between providers
- **Transparent**: Response format is consistent regardless of provider

## Architecture
```
Cloud Provider Manager
├── Provider Registry
├── Provider Selector
├── Provider Factory
│   ├── StubCloudProvider (testing)
│   ├── OpenAICompatibleProvider
│   └── ClaudeProvider (future)
└── Credential Manager
```

## Components
- **CloudProvider (Abstract)**: Base interface with execute, stream, health, models methods
- **Provider Registry**: Available providers and their configurations
- **Provider Factory**: Creates provider instances from config
- **Credential Manager**: Manages encrypted API key storage
- **Health Monitor**: Tracks provider availability and latency
- **Usage Tracker**: Logs token usage and costs

### Provider Implementations
| Provider | Type | Status |
|----------|------|--------|
| StubCloudProvider | Test double | Implemented |
| OpenAICompatibleProvider | API | Implemented |
| ClaudeProvider | API | Future |
| GeminiProvider | API | Future |

## Data Flow
Request → Provider Selector → Credential Manager → Provider.execute(prompt) → Normalized Response

## Public Interfaces
- `POST /cloud/execute` → Send request to cloud provider
- `GET /cloud/providers` → List configured providers
- `POST /cloud/providers/select` → Set active provider
- `GET /cloud/status` → Provider health status
- `GET /cloud/usage` → Usage and cost statistics

## Configuration
- Cloud config file: `~/.igris/cloud.yaml`
- Provider definitions with endpoint, model, and auth info
- API keys stored in encrypted credential store: `~/.igris/credentials/`
- Provider priority order for failover

## Dependencies
- HTTP client (aiohttp, httpx)
- PIE (anonymization before cloud calls)
- Credential Store (encrypted key storage)

## Security Considerations
- API keys are stored encrypted (AES-256)
- API keys are never logged or exposed in responses
- Request content is anonymized by PIE before sending
- HTTPS is required for all provider communication
- Token usage tracking prevents billing surprises

## Failure Recovery
- Provider timeout → retry (2 attempts) → failover to next provider
- Authentication failure → alert user to check credentials
- Rate limit hit → exponential backoff
- All providers failed → fallback to local inference

## Future Improvements
- Phase 2: Automatic provider failover
- Phase 3: Cost-based provider selection
- Phase 4: Multi-provider response ensemble

## Engineering Notes
The cloud provider abstraction makes it possible to add new providers without touching any other part of the system.

## Acceptance Criteria
- All providers implement the same abstract interface
- Provider can be switched at runtime
- API keys are stored encrypted
- Provider health is monitored and reported
- Local fallback works when all providers are unavailable

## References
- Volume-4-Infrastructure/03-Hybrid-Intelligence.md
- volume-4-Infrastructure/05-Storage.md (credential store)
- app/runtime/cloud_provider.py
