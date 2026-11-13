# Testing

## Purpose
Define the testing strategy, requirements, and practices for the IRIS project.

## Responsibilities
- Define testing levels and coverage targets
- Establish test naming and structure conventions
- Document test infrastructure and tools
- Guide continuous integration testing
- Ensure quality through automated testing

## Design Goals
- **Automated**: Tests run in CI without manual intervention
- **Fast**: Test suite completes in under 10 minutes
- **Reliable**: Tests are deterministic and not flaky
- **Comprehensive**: Cover unit, integration, and E2E levels

## Components

### Test Levels
| Level | Scope | Target Coverage | Tools |
|-------|-------|-----------------|-------|
| Unit | Individual functions/classes | > 80% | pytest, vitest |
| Integration | Component interactions | > 60% | pytest, supertest |
| E2E | Full user workflows | Critical paths | Playwright |
| Security | Vulnerability scanning | — | bandit, npm audit |

### Test Structure
```
tests/
├── unit/
│   ├── api/
│   ├── app/
│   └── website/
├── integration/
│   ├── api/
│   └── app/
├── e2e/
│   └── workflows/
└── security/
```

### Naming Convention
- Test files: `<module>.test.<ext>` (e.g., `auth.test.py`)
- Test functions: `test_<function>_<scenario>` (e.g., `test_login_with_valid_credentials`)
- Test classes: `Test<Component>` (e.g., `TestAuthRouter`)

## Data Flow
Code Change → Lint → Unit Tests → Integration Tests → E2E Tests → Security Scan → Deploy

## Public Interfaces
- `pytest api/ app/` — Run Python tests
- `npm test` — Run frontend tests
- `npx playwright test` — Run E2E tests
- `bandit -r api/ app/` — Security scanning

## Configuration
- Python: `pytest.ini` with coverage configuration
- TypeScript: `jest.config.js` or `vitest.config.ts`
- E2E: `playwright.config.ts`
- Coverage threshold: `> 80%` for unit, `> 60%` for integration
- CI: GitHub Actions workflow

## Dependencies
- pytest (Python testing)
- pytest-asyncio (async testing)
- vitest/jest (TypeScript testing)
- Playwright (E2E testing)
- bandit (Python security scanning)

## Security Considerations
- Tests never use production data or secrets
- Test databases are isolated
- Security scanning is part of CI
- Tests verify authentication and authorization

## Failure Recovery
- Test failure → block merge → report to developer
- Flaky test → quarantine → fix or remove
- CI timeout → optimize slow tests

## Future Improvements
- Phase 2: Performance/load testing
- Phase 3: Fuzz testing for security
- Phase 4: Visual regression testing

## Engineering Notes
Write tests as you write code, not after. Test behavior, not implementation.

## Acceptance Criteria
- Unit test coverage > 80% for new code
- Integration tests cover all API endpoints
- E2E tests cover critical user flows
- Tests run in CI on every PR
- Security scanning passes before merge

## References
- Volume-6-Engineering/01-Coding-Standards.md
- Volume-6-Engineering/06-Code-Review.md
