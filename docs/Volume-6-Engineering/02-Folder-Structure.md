# Folder Structure

## Purpose
Define the project directory structure, conventions, and organization principles for the IGRIS codebase.

## Responsibilities
- Document the canonical folder structure
- Define what goes in each directory
- Establish naming conventions for files and directories
- Guide new contributors on navigation

## Design Goals
- **Logical**: Structure mirrors system architecture
- **Navigable**: Contributors find files quickly
- **Scalable**: Structure accommodates growth
- **Consistent**: Same pattern across all domains

## Components

### Root Structure
```
IGRIS-AI/
├── api/                  # FastAPI backend server
│   ├── core/            # Core config, database, security
│   ├── routers/         # API endpoint definitions
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── models/          # SQLAlchemy models
│   └── main.py          # Application entry point
├── app/                  # IGRIS AI Engine
│   ├── core/            # Core engine, AI loop, skills
│   ├── runtime/         # Inference, models, memory, voice
│   ├── pie/             # Privacy Intelligence Engine
│   ├── installer/       # Installation scripts
│   └── server.py        # Engine server entry point
├── website/              # Next.js frontend
│   ├── app/             # Next.js 14 app router pages
│   ├── components/      # React components
│   ├── lib/             # Utilities, API client
│   ├── public/          # Static assets
│   └── styles/          # Global styles
├── docs/                 # Documentation
│   ├── Volume-0-Foundation/
│   ├── Volume-1-Architecture/
│   ├── Volume-2-Intelligence/
│   ├── Volume-3-Capabilities/
│   ├── Volume-4-Infrastructure/
│   ├── Volume-5-Security/
│   ├── Volume-6-Engineering/
│   └── Volume-7-Roadmap/
├── .github/              # GitHub workflows, templates
├── scripts/              # Development and build scripts
├── tests/                # Test files
└── configs/              # Shared configuration examples
```

### Naming Conventions
- Directories: PascalCase (e.g., `Volume-1-Architecture`)
- Python files: snake_case (e.g., `model_manager.py`)
- TypeScript files: kebab-case (e.g., `api-client.ts`)
- React components: PascalCase (e.g., `DashboardCard.tsx`)
- Test files: `<module>.test.<ext>` (e.g., `auth.test.py`)

## Data Flow
Code flows from entry points → routers → services → models/backends

## Public Interfaces
No interfaces — this is an organizational convention.

## Configuration
No configuration — structure is enforced by convention.

## Dependencies
None — structure is self-contained.

## Security Considerations
- Sensitive directories (credentials, keys) are in `.gitignore`
- `__pycache__`, `.venv`, `node_modules` are in `.gitignore`
- `.env` files are never committed

## Failure Recovery
If the structure drifts, a refactoring PR should restore the standard layout.

## Future Improvements
- Phase 2: Monorepo tool integration (Nx, Turborepo)
- Phase 3: Code generation for new components

## Engineering Notes
Don't fight the structure. Put code where it belongs, not where it's convenient.

## Acceptance Criteria
- All code is in its designated directory
- New modules follow naming conventions
- `.gitignore` covers all generated/transient directories
- Contributors can find files without asking

## References
- Volume-6-Engineering/01-Coding-Standards.md
- IGRIS.md (root-level mapping)
