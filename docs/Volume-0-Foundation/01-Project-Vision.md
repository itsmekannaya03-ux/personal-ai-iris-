# Project Vision

## Purpose
Define the long-term product vision for IGRIS as a Personal AI Operating System that competes with the world's best AI assistants while preserving complete user privacy.

## Responsibilities
- Articulate the product category and market position
- Define target users and use cases
- Describe the evolution from Phase 1 to Phase 4
- Guide product strategy and roadmap priorities

## Design Goals
- **Ambitious**: IGRIS is not a chatbot, it is a Personal AI Operating System
- **Achievable**: The vision is grounded in realistic engineering phases
- **Differentiated**: Privacy-first, local-first, intelligence-first

## Architecture
From user perspective: User → IGRIS OS → IGRIS Runtime → PIE → Model Manager → Inference Engine → AI Model

## Components
- **IGRIS OS**: The shell and interface layer
- **IGRIS Runtime**: Core orchestration engine
- **PIE**: Privacy Intelligence Engine
- **Model Manager**: Intelligent model selection
- **Inference Engine**: Abstracted AI model execution

## Data Flow
User input → Intent detection → Privacy classification → Model selection → Inference → Response with context

## Public Interfaces
CLI interface, local HTTP API on port 5743, Web dashboard on port 3000.

## Configuration
Vision is realized through product roadmap in Volume 7.

## Dependencies
Open-source foundation models (Phase 1), custom IGRIS M1/M2 models (Phase 2-3), IGRIS Foundation Model (Phase 4).

## Security Considerations
Privacy-first architecture ensures all data processing happens locally by default.

## Failure Recovery
If a phase fails technically, the architecture supports fallback to earlier phases.

## Future Improvements
Phase 2 will introduce IGRIS M1 fine-tuning. Phase 3 will introduce IGRIS M2. Phase 4 will train an original foundation model.

## Engineering Notes
Every feature should be evaluated against its contribution to long-term vision.

## Acceptance Criteria
- Users can install IGRIS without touching Ollama or any inference engine
- PIE makes intelligent privacy decisions without user intervention after the first few weeks
- Model Manager selects the best model without user manual selection
- All components are replaceable without redesigning the system

## References
- Volume-7-Roadmap/01-Commercial-Roadmap.md
- 00-Manifesto.md
