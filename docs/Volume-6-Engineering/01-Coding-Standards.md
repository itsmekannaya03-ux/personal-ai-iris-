# Coding Standards

## Purpose
Define the coding standards for all IRIS code — style, naming conventions, documentation, and quality requirements.

## Responsibilities
- Ensure consistent code style across the project
- Define naming conventions for all languages
- Establish documentation requirements
- Set quality and linting standards

## Design Goals
- **Consistent**: All code looks like it was written by one person
- **Readable**: Code is optimized for human reading
- **Maintainable**: Standards reduce long-term maintenance costs
- **Automated**: Style is enforced by tooling, not manual review

## Components

### Python Standards
- **Style**: PEP 8 (Black formatter, line length 100)
- **Typing**: All functions have type annotations
- **Docstrings**: Google-style docstrings for public APIs
- **Imports**: isort with Black-compatible settings
- **Linting**: ruff with strict rules
- **Naming**: snake_case for functions/variables, PascalCase for classes

### TypeScript/JavaScript Standards
- **Style**: Prettier (line length 100)
- **Typing**: TypeScript strict mode
- **Naming**: camelCase for functions/variables, PascalCase for components
- **Imports**: Organized by external → internal, absolute → relative
- **Linting**: ESLint with TypeScript rules

### General Standards
- No commented-out code
- No print/console.log statements in committed code
- Error messages are user-friendly
- Magic strings use named constants
- Complex logic has comments explaining why, not what
- Functions do one thing (single responsibility)

## Data Flow
Code → Linter → Formatter → Type Check → Review → Merge

## Public Interfaces
- Configuration files: `.pre-commit-config.yaml`, `pyproject.toml`, `.eslintrc.js`
- Lint commands: `ruff check .`, `eslint .`
- Format commands: `black .`, `prettier --write .`

## Configuration
- Python: `pyproject.toml` (Black, ruff, mypy settings)
- TypeScript: `.eslintrc.js`, `tsconfig.json`, `.prettierrc`
- Pre-commit hooks: `.pre-commit-config.yaml`
- Editor config: `.editorconfig`

## Dependencies
- Python: Black, ruff, mypy, isort
- TypeScript: ESLint, Prettier, TypeScript
- Pre-commit

## Security Considerations
- Linting rules include security checks
- No hardcoded secrets allowed
- Input validation is required in all public APIs
- SQL injection prevention is mandatory

## Failure Recovery
- Linting violations block commits (pre-commit hooks)
- Formatting issues are auto-fixed where possible
- Type errors must be fixed before merge

## Future Improvements
- Phase 2: Automated code quality scoring
- Phase 3: Architecture rule enforcement

## Engineering Notes
Follow the principle: "Always code as if the person who ends up maintaining your code is a violent psychopath who knows where you live."

## Acceptance Criteria
- All code passes linting before merge
- Type annotations exist on all Python functions
- TypeScript strict mode passes
- Pre-commit hooks are configured and working
- Documentation follows Google style for Python

## References
- Volume-6-Engineering/06-Code-Review.md
- Volume-6-Engineering/05-Testing.md
