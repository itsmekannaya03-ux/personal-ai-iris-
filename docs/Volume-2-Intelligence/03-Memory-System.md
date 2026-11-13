# Memory System

## Purpose
Define the Memory System — the three-tier memory architecture that enables IRIS to remember context across sessions, recall facts, and preserve important information permanently.

## Responsibilities
- Store and retrieve conversation context (short-term)
- Preserve important facts across sessions (long-term)
- Archive critical information permanently (deep memory)
- Support semantic search via vector embeddings
- Prune irrelevant memories automatically

## Design Goals
- **Tiered**: Three memory tiers with different retention policies
- **Searchable**: Semantic search across all memory tiers
- **Persistent**: Memory survives system restarts
- **Private**: Deep memory is encrypted

## Architecture
```
Memory System
├── Short-Term Memory (STM)
│   ├── In-memory buffer (last N turns)
│   ├── Ephemeral: cleared after session timeout
│   └── Used for immediate context
│
├── Long-Term Memory (LTM)
│   ├── ChromaDB vector store
│   ├── Semantic search by embedding
│   ├── Persisted to disk
│   └── Auto-summarization for compression
│
└── Deep Memory
    ├── Encrypted JSON store
    ├── Manual save / AI-proposed
    ├── AES-256 encrypted
    └── User-confirmed preservation
```

## Components
- **STM Buffer**: In-memory circular buffer of last N turns
- **Embedder**: Generates text embeddings for semantic search
- **Vector Store**: ChromaDB for LTM storage and retrieval
- **Summarizer**: Compresses LTM entries to save space
- **Deep Store**: Encrypted file-based permanent storage
- **Pruner**: Removes irrelevant or old LTM entries
- **Memory Backend Adapter**: Abstract interface wrapping MemoryManager

## Data Flow
All modules → MemorySystem.store(context) → STM → LTM (auto-promote) → Deep Memory (manual)

Query → Semantic Search → LTM results + STM results + Deep Memory results → Merged Context

## Public Interfaces
- `MemorySystem.store(key, value, tier) -> bool`
- `MemorySystem.query(query, tier) -> list[Memory]`
- `MemorySystem.semantic_search(query, limit) -> list[Memory]`
- `MemorySystem.promote_to_deep(key) -> bool`
- `MemorySystem.forget(key) -> bool`
- `MemorySystem.clear(tier) -> bool`
- `GET /memory/status` → Memory system health and stats
- `POST /memory/search` → Semantic search endpoint

## Configuration
- STM buffer size: `stm_buffer_size` (default: 50 turns)
- LTM retention: `ltm_retention_days` (default: 365)
- Deep memory encryption: `deep_memory_encrypt` (default: true)
- Embedding model: `embedding_model` (configured in model registry)

## Dependencies
- ChromaDB (vector store)
- Embedding model (via Inference Engine)
- AES encryption library (deep memory)
- `memory_backend.py` adapter pattern

## Security Considerations
- Deep memory is AES-256 encrypted
- Memory content is never sent to cloud providers
- PIE classification gates what gets stored
- Users can delete any memory at any time
- Memory exports are encrypted by default

## Failure Recovery
- ChromaDB connection failure → STM-only mode (degraded)
- Embedding model unavailable → keyword-based fallback
- Deep memory corruption → restore from backup
- Memory store full → LRU eviction of oldest LTM entries

## Future Improvements
- Phase 2: Cross-device memory synchronization
- Phase 3: Associative memory networks
- Phase 4: Episodic memory with temporal reasoning

## Engineering Notes
Memory is the most performance-critical intelligence module. Query latency directly impacts user experience.

## Acceptance Criteria
- STM recall time < 5ms
- LTM semantic search < 100ms
- Deep memory retrieval < 50ms
- Memory survives engine restart
- Encrypted deep memory cannot be read without key

## References
- Volume-4-Infrastructure/05-Storage.md
- Volume-2-Intelligence/01-Privacy-Intelligence-Engine.md
- app/runtime/memory_backend.py
