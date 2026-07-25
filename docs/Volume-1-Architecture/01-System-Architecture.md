# System Architecture

## Purpose
Define the overall system architecture of IGRIS, including all major components, their interactions, and deployment topology.

## Responsibilities
- Document all system components and their boundaries
- Define communication pathways between components
- Establish deployment architecture
- Guide system evolution and scaling

## Design Goals
- **Modular**: Components are independently deployable and replaceable
- **Secure**: All inter-component communication is authenticated and authorized
- **Observable**: Every component exposes health, metrics, and logs
- **Resilient**: System continues operating when components fail

## Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Frontend (:3000)                     │
│                    (Next.js 14 / React / Tailwind)               │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP (Next.js rewrites)
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                     API Server (:8001)                            │
│  (FastAPI / PostgreSQL / JWT Auth / Stripe)                      │
│  Routers: auth, payments, subscriptions, clones                  │
└──────────────┬────────────────────────────────────┬──────────────┘
               │ REST API                           │ REST API
               ▼                                    ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│   IGRIS Engine (:5743)       │  │   External Cloud API         │
│   FastAPI Server             │  │   (via PIE routing)          │
│   ┌──────────────────────┐   │  │                              │
│   │      PIE              │   │  │                              │
│   │  ┌────────────────┐   │   │  │                              │
│   │  │ Classifier     │   │   │  │                              │
│   │  │ Router         │   │   │  │                              │
│   │  │ Anonymizer     │   │   │  │                              │
│   │  │ Learner        │   │   │  │                              │
│   │  │ Profile        │   │   │  │                              │
│   │  └────────────────┘   │   │  │                              │
│   │                       │   │  │                              │
│   │  ┌──────────────────┐ │   │  │                              │
│   │  │ Runtime           │ │   │  │                              │
│   │  │ Model Manager     │ │   │  │                              │
│   │  │ Inference Engine  │ │   │  │                              │
│   │  │ Memory Backend    │ │   │  │                              │
│   │  │ Voice Backend     │ │   │  │                              │
│   │  └──────────────────┘ │   │  │                              │
│   └──────────────────────┘   │  │                              │
└──────────────────────────────┘  └──────────────────────────────┘
               │
               ▼
         ┌─────────────┐
         │  Ollama      │  ┌───────────┐
         │  (Local LLM) │  │ ChromaDB   │
         └─────────────┘  └───────────┘
```

## Components
- **Web Frontend**: Next.js 14 application with authentication, dashboard, pricing, settings
- **API Server**: FastAPI server handling user management, subscriptions, payments
- **IGRIS Engine**: Core AI engine with PIE, Runtime, skills, memory, and voice systems
- **PIE**: Privacy Intelligence Engine for intelligent privacy routing
- **Runtime**: Model manager, inference engine, memory and voice backends
- **External Services**: Cloud providers (via PIE routing), Stripe (payments)

## Data Flow
User → Web Frontend (:3000) → Next.js rewrites → API Server (:8001) → IGRIS Engine (:5743) → Local Models (Ollama) / Cloud (via PIE)

## Public Interfaces
- Frontend: HTTP on port 3000
- API: HTTP on port 8001 with JWT authentication
- Engine: HTTP on port 5743 with token authentication
- CLI: local command-line interface

## Configuration
Architecture configuration in environment variables and config files per component.

## Dependencies
- PostgreSQL for user data
- ChromaDB for vector memory
- Ollama for local model inference (abstracted behind InferenceEngine)
- Next.js 14, FastAPI, Python 3.11+

## Security Considerations
- Frontend-API communication uses JWT tokens
- Engine-to-API communication uses shared secret
- PIE ensures privacy-sensitive data never reaches cloud providers
- All secrets stored in environment variables, never in code

## Failure Recovery
- API server restart is stateless (session in JWT)
- Engine restart preserves memory in ChromaDB
- Frontend error boundaries catch rendering failures

## Future Improvements
- Phase 2: Horizontal scaling for API server
- Phase 3: Engine clustering for distributed inference
- Phase 4: Cloud-edge hybrid deployment

## Engineering Notes
The architecture follows a clean separation between data (API) and intelligence (Engine) planes.

## Acceptance Criteria
- Each component can be started independently
- Component failure does not cascade to other components
- Adding a new component requires no changes to existing components
- All inter-component communication is documented and versioned

## References
- Volume-1-Architecture/06-Boot-Sequence.md
- Volume-1-Architecture/08-Communication-Flow.md
- Volume-4-Infrastructure/05-Storage.md
