# Contributing

## Purpose
Define how to contribute to the IRIS project — from setting up a development environment to submitting changes and engaging with the community.

## Responsibilities
- Guide new contributors through setup
- Define contribution workflow
- Document development environment setup
- Establish community guidelines
- Provide onboarding path

## Design Goals
- **Welcoming**: Low barrier for first contribution
- **Clear**: Every step is documented
- **Structured**: Clear process for different contribution types
- **Rewarding**: Contributors see their impact

## Components

### Getting Started
1. Read the Manifesto (Volume-0/00-Manifesto.md)
2. Read the terminology guide (Volume-0/04-Terminology.md)
3. Set up development environment
4. Find a good first issue (labeled `good-first-issue`)
5. Create a branch and make changes
6. Submit a pull request

### Development Environment
```bash
# Clone repository
git clone https://github.com/iris/IRIS-AI.git
cd IRIS-AI

# Backend setup
cd api
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Engine setup
cd app
pip install -r requirements.txt

# Frontend setup
cd website
npm install
```

### Contribution Types
| Type | Description | Process |
|------|-------------|---------|
| Bug fix | Fix a bug | Open issue, submit PR |
| Feature | New functionality | Discuss in issue first |
| Documentation | Improve docs | Submit PR directly |
| Design | UI/UX improvements | Discuss in issue first |
| Research | Investigation | Post findings in discussion |

### Community Guidelines
- Be respectful and inclusive
- Assume good intent
- Provide constructive feedback
- Give credit to others' work
- Follow the Code of Conduct

## Data Flow
Issue → Discussion → Assignment → Development → PR → Review → Merge

## Public Interfaces
- Issues: bug reports, feature requests
- Discussions: questions, ideas, research
- Pull Requests: code changes
- Wiki: community documentation

## Configuration
- Issue templates: `.github/ISSUE_TEMPLATE/`
- PR template: `.github/PULL_REQUEST_TEMPLATE.md`
- Code of Conduct: `.github/CODE_OF_CONDUCT.md`

## Dependencies
- Git and GitHub
- Development tools (Python 3.11+, Node.js 18+)
- IRIS Neural Core (for local model development)

## Security Considerations
- Report security issues privately (security@iris.com / placeholder)
- Never commit secrets even in example code
- Follow security best practices from Volume 5

## Failure Recovery
- Setup issues → check troubleshooting guide in repo
- Merge conflicts → rebase feature branch
- Questions → ask in GitHub Discussions

## Future Improvements
- Phase 2: Contributor recognition program
- Phase 3: Automated onboarding for common setups
- Phase 4: Community-contributed plugin marketplace

## Engineering Notes
Good documentation is the best way to attract contributors.

## Acceptance Criteria
- New developer can set up and run project in under 30 minutes
- First-time contributors can find a good first issue
- PR template guides proper submissions
- Community guidelines are clear and enforced
- Issue templates cover all contribution types

## References
- Volume-6-Engineering/03-Git-Workflow.md
- Volume-6-Engineering/06-Code-Review.md
- Volume-0-Foundation/00-Manifesto.md
