# Model Registry

## Purpose
Define the Model Registry — the central catalog that manages AI model metadata, versions, routing rules, and availability for the IRIS Runtime.

## Responsibilities
- Catalog all available AI models with metadata
- Define task-to-model routing rules
- Manage model versioning and compatibility
- Track model availability and health
- Provide model upgrade path suggestions

## Design Goals
- **Centralized**: Single source of truth for model metadata
- **Flexible**: Routing rules can be customized per task
- **Upgradable**: Clear migration paths between model versions
- **Observable**: Model health and performance tracked

## Architecture
```
Model Registry
├── Model Catalog
│   ├── Model metadata (name, version, size, capabilities)
│   ├── Hardware requirements
│   └── Download source and checksums
├── Task Router
│   ├── Task-to-model mappings
│   ├── Fallback chains
│   └── Priority rules
└── Upgrade Manager
    ├── Available upgrades
    ├── Compatibility matrix
    └── Download suggestions
```

## Components
- **Model Catalog**: Database of all known models with metadata
- **Task Router**: Maps tasks (reasoning, chat, coding, etc.) to optimal models
- **Fallback Manager**: Defines fallback chains when primary model unavailable
- **Upgrade Manager**: Suggests model upgrades based on hardware and needs
- **Health Tracker**: Monitors loaded model health and performance

## Data Flow
Task Request → Task Router → Model Selection → Availability Check → Fallback (if needed) → Model Load → Inference

## Public Interfaces
- `GET /models/list` → List all registered models
- `GET /models/<name>/info` → Model metadata
- `GET /models/search` → Search models by capability
- `GET /models/upgrade-path` → Get upgrade suggestions
- `GET /models/missing` → List recommended but missing models
- `POST /models/refresh` → Refresh model catalog

## Configuration
- Model registry file: `~/.iris/models.yaml`
- Default model per task type
- Fallback chain order per task
- Minimum model size for each task

## Dependencies
- IRIS Neural Core (model provider for local inference)
- Runtime Model Manager (model selection)
- Local file system (model storage)

## Security Considerations
- Model files are verified by checksum after download
- Model manifests are signed (future)
- Models from untrusted sources are flagged
- Model execution respects resource limits

## Failure Recovery
- Missing model → check fallback chain → suggest download → use fallback
- Corrupted model → delete and re-download
- Model health check failure → unload and use fallback

## Future Improvements
- Phase 2: Model download progress and resume
- Phase 3: Automatic model optimization (quantization)
- Phase 4: Model marketplace for custom models

## Engineering Notes
Models are the most resource-intensive component. Always prefer the smallest model that meets quality requirements.

## Acceptance Criteria
- Model catalog contains all available models
- Task-to-model routing selects the correct model
- Fallback chains work when primary model is unavailable
- Upgrade path lists clear, actionable suggestions
- Model health is tracked and reported

## References
- Volume-4-Infrastructure/02-Model-Benchmark-System.md
- Volume-1-Architecture/05-Runtime.md
- app/runtime/model_manager.py
