# Git Workflow

## Purpose
Define the Git workflow, branching strategy, and commit conventions for the IRIS project.

## Responsibilities
- Document branching strategy
- Define commit message format
- Establish pull request process
- Guide release management

## Design Goals
- **Simple**: Easy to understand and follow
- **Consistent**: All commits follow the same format
- **Traceable**: Every commit links to an issue or purpose
- **Safe**: Main branch is always deployable

## Components

### Branching Strategy
```
main          ← Production-ready code
  └── dev     ← Integration branch
       ├── feat/<name>    ← New features
       ├── fix/<name>     │ Bug fixes
       ├── docs/<name>    │ Documentation
       ├── refactor/<name>│ Code refactoring
       └── chore/<name>   └─ Maintenance tasks
```

### Commit Convention (Conventional Commits)
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`, `perf`

Examples:
- `feat(auth): add JWT refresh token endpoint`
- `fix(pie): correct privacy level for medical queries`
- `docs(volume-4): add monitoring architecture doc`
- `refactor(runtime): extract model manager from inference engine`

### Pull Request Process
1. Create feature branch from `dev`
2. Implement changes with atomic commits
3. Run tests and linting locally
4. Push branch and create PR to `dev`
5. Request review (2 reviewers for core changes)
6. Address review feedback
7. Merge after approval (squash merge)

## Data Flow
Local → Feature Branch → PR → Review → Merge to dev → Release → Merge to main

## Public Interfaces
- Branch naming: `type/description` (kebab-case)
- Commit format: `type(scope): description` (lowercase)
- PR title: Same as commit format

## Configuration
- `.gitignore` covers all generated files
- `.github/PULL_REQUEST_TEMPLATE.md` for PR template
- Branch protection on `main` and `dev`

## Dependencies
- Git (version control)
- GitHub (remote repository)

## Security Considerations
- Never commit secrets or credentials
- `.env` files are in `.gitignore`
- API keys are detected by pre-commit hooks
- Commit signatures are encouraged (GPG)

## Failure Recovery
- Broken commit → `git revert` (never force push to shared branches)
- Merge conflict → resolve in feature branch
- Accidental push to main → revert immediately

## Future Improvements
- Phase 2: Automated release changelog generation
- Phase 3: Conventional commit linting in CI

## Engineering Notes
Commit early, commit often. Squash merge keeps history clean.

## Acceptance Criteria
- All commits follow conventional commit format
- Feature branches branch from `dev`
- PRs require review before merge
- Main branch is protected
- `.gitignore` prevents accidental secret commits

## References
- Volume-6-Engineering/06-Code-Review.md
- Volume-6-Engineering/07-Contributing.md
