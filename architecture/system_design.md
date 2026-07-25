# System Design

## Purpose
Define the overall system design, architecture decisions, and component interactions for IGRIS.

## Responsibilities
- Document system architecture and design decisions
- Define component boundaries and interfaces
- Guide implementation and integration

## Design Goals
- Modular, secure, observable, and resilient architecture
- Privacy-first design with local-by-default processing
- Extensible plugin and skill system

## Architecture
Refer to Volume-1-Architecture for detailed architecture documentation.

## Components
- Web Frontend (Next.js 14)
- Backend API (FastAPI)
- AI Engine (IGRIS Runtime)
- Privacy Intelligence Engine (PIE)
- Memory System (ChromaDB)
- Model Manager (Ollama / Cloud)

## Data Flow
User → Frontend → API → Engine → PIE → Model → Response

## Public Interfaces
- Frontend: port 3000
- API: port 8001
- Engine: port 5743

## Configuration
Environment-based configuration. See `.env.example`.

## Dependencies
- PostgreSQL, ChromaDB, Ollama, Next.js, FastAPI

## Security Considerations
JWT authentication, API tokens, PIE privacy routing, encryption at rest.

## Failure Recovery
Stateless API, persistent memory, graceful degradation.

## Future Improvements
Phase 2: IGRIS M1 model, Phase 3: Multi-modal, Phase 4: Foundation model.

## Acceptance Criteria
All components independently deployable, no cascading failures.

## References
- docs/Volume-1-Architecture/
- docs/Volume-5-Security/
