# Runtime

## Purpose
Define the IRIS Runtime - the foundational execution layer that provides inference, model management, memory, and voice capabilities.

## Responsibilities
- Execute AI model inference through abstracted engine interface
- Manage model selection and loading/unloading
- Provide vector and persistent memory backends
- Deliver text-to-speech and speech-to-text capabilities
- Expose runtime status and health information

## Design Goals
- **Engine-agnostic**: Swap inference engines without code changes
- **Model-optimized**: Select the best model for each task
- **Memory-persistent**: Survive restarts with full memory state
- **Voice-extensible**: Support multiple TTS/STT backends

## Architecture
```
Runtime
├── Inference Engine (Abstract)
│   ├── IRIS Neural CoreEngine
│   └── CloudProvider (StubCloudProvider, OpenAICompatibleProvider)
├── Model Manager
│   ├── Task-based routing
│   ├── Fallback chains
│   └── Upgrade path suggestions
├── Memory Backend (Abstract)
│   ├── ChromaDB adapter
│   └── MemoryManager integration
└── Voice Backend (Abstract)
    ├── pyttsx3 adapter
    └── Fallback stub
```

## Components
- **Inference Engine**: Abstract base class with execute(), stream(), and health() methods
- **Model Manager**: Routes tasks to optimal models with fallback chains
- **Memory Backend**: Adapter wrapping MemoryManager with persistence
- **Voice Backend**: Adapter wrapping VoiceEngine with TTS support

## Data Flow
Task → Model Manager → Model Selection → Inference Engine → Response → Memory Backend (context update)

## Public Interfaces
- `POST /runtime/status` → Returns full runtime health, model list, PIE mode, cloud provider, privacy profile
- `InferenceEngine.execute(prompt, context) -> Response`
- `ModelManager.get_upgrade_path() -> list[ModelSuggestion]`
- `ModelManager.get_missing_models() -> list[str]`
- `MemoryBackend.store(key, value) -> bool`
- `VoiceBackend.speak(text) -> None`

## Configuration
- Model registry: `~/.iris/models.yaml`
- Default model: `llama3.2:3b`
- Cloud provider config: `~/.iris/cloud.yaml`
- Voice backend selection: `voice_backend` in config

## Dependencies
- IRIS Neural Core for local model inference
- ChromaDB for vector memory
- pyttsx3 for TTS
- Abstract base classes for extensibility

## Security Considerations
- Inference engine never logs raw prompts
- Cloud provider uses encrypted API key storage
- Memory backend supports encryption for sensitive data

## Failure Recovery
- Model missing → check upgrade path → suggest download → fallback to smaller model
- Inference timeout → retry with smaller model
- Memory backend failure → log warning, continue with reduced memory

## Future Improvements
- Phase 2: GPU acceleration detection and optimization
- Phase 3: Distributed inference across multiple machines
- Phase 4: Custom compiled inference engine

## Engineering Notes
The Runtime is the only component that directly interacts with AI models. All other components go through Runtime.

## Acceptance Criteria
- Change inference engine by changing one config value
- Model Manager selects correct model for each task type
- Memory survives engine restart
- Voice backend can be hot-swapped
- Runtime status endpoint returns all required diagnostic info

## References
- Volume-4-Infrastructure/01-Model-Registry.md
- Volume-4-Infrastructure/04-Cloud-Providers.md
- Volume-3-Capabilities/03-Voice-System.md
- Volume-2-Intelligence/03-Memory-System.md
