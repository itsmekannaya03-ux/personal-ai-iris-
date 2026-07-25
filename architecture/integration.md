# Integration

## Purpose
Define integration patterns and strategies between IGRIS components.

## Responsibilities
- Document inter-component communication
- Define API contracts
- Manage dependency coordination

## Architecture
Frontend ↔ API (REST, JWT) ↔ Engine (REST, Token) ↔ Models (Ollama API / Cloud API)

## Components
- API Client (website/lib/api.ts)
- Engine Client
- Cloud Provider Abstraction

## Public Interfaces
REST APIs with JSON payloads. OpenAPI documentation.

## Dependencies
All components depend on well-defined interfaces, not implementations.
