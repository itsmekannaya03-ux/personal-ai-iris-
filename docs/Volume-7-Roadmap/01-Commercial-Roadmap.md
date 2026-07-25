# Commercial Roadmap

## Purpose
Define the product evolution roadmap for IGRIS across four phases — from foundational release to fully autonomous AI operating system.

## Responsibilities
- Define product milestones and release timeline
- Establish market positioning and go-to-market strategy
- Guide resource allocation across phases
- Track progress toward commercial goals

## Design Goals
- **Achievable**: Each phase builds on the previous
- **Value-driven**: Each phase delivers user value
- **Market-aware**: Roadmap responds to market conditions
- **Investor-ready**: Clear progression to commercialization

## Architecture
```
Phase 1 (Current) → Phase 2 (IGRIS M1) → Phase 3 (IGRIS M2) → Phase 4 (Foundation Model)
```

## Components

### Phase 1: Foundation (Current)
- **Focus**: Core architecture, privacy engine, basic skills
- **Deliverables**:
  - Working PIE with adaptive learning
  - 8 built-in skills
  - Web dashboard (auth, chat, settings)
  - API server with PostgreSQL
  - CLI interface
  - Cross-platform installer
- **Timeline**: Q3 2026
- **Target Users**: Early adopters, developers, privacy enthusiasts
- **Monetization**: Free (open source)

### Phase 2: IGRIS M1
- **Focus**: Fine-tuned model, enhanced intelligence
- **Deliverables**:
  - IGRIS M1 fine-tuned model
  - Enhanced memory system
  - Plugin system
  - Voice conversations with wake word
  - Developer mode with sandboxed code execution
  - Basic subscription model
- **Timeline**: Q1 2027
- **Target Users**: Power users, developers
- **Monetization**: Freemium (free tier + subscription for cloud features)

### Phase 3: IGRIS M2
- **Focus**: Advanced capabilities, commercial readiness
- **Deliverables**:
  - IGRIS M2 with multi-modal capabilities
  - Vision system
  - Desktop and browser automation
  - Cloud sync (end-to-end encrypted)
  - Team/collaboration features
  - Phone casting / mobile companion
  - Premium subscription tier
- **Timeline**: Q3 2027
- **Target Users**: Professionals, teams
- **Monetization**: Subscription (individual + team tiers)

### Phase 4: IGRIS Foundation Model
- **Focus**: Original foundation model, full AI OS
- **Deliverables**:
  - IGRIS Foundation Model (trained from scratch)
  - Autonomous operation
  - Multi-device mesh
  - Enterprise features
  - Marketplace for skills and models
- **Timeline**: 2028+
- **Target Users**: Enterprise, all users
- **Monetization**: Subscription + enterprise licensing

## Data Flow
Phase gates → Feature prioritization → Development → Release → Feedback → Next phase

## Public Interfaces
- Public roadmap on website
- Changelog per release
- Community feedback channels

## Configuration
Roadmap is managed in project management system (GitHub Projects).

## Dependencies
- Volume-7-Roadmap/02-IGRIS-M1.md (Phase 2)
- Volume-7-Roadmap/06-Long-Term-Vision.md (Phase 4)
- Volume-0-Foundation/01-Project-Vision.md

## Security Considerations
- Security improvements are prioritized each phase
- Commercial features maintain privacy guarantees
- Subscription data is protected

## Failure Recovery
- Phase delay → descope non-essential features
- Market shift → reprioritize roadmap
- Technical blocker → invest in research

## Future Improvements
Phases are the future improvements by definition.

## Engineering Notes
The roadmap is a guide, not a contract. Adapt as you learn.

## Acceptance Criteria
- Each phase has defined deliverables and timeline
- Phase 1 is fully implemented
- Phase 2 has detailed specification
- Phase 3-4 have research and exploration only
- Roadmap is communicated publicly

## References
- Volume-0-Foundation/01-Project-Vision.md
- Volume-7-Roadmap/06-Long-Term-Vision.md
