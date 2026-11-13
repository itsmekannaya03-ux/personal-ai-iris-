# Code Review

## Purpose
Define the code review process, standards, and checklist for ensuring code quality across the IRIS project.

## Responsibilities
- Establish code review process
- Define review checklist
- Guide constructive feedback practices
- Ensure consistent review quality
- Document approval requirements

## Design Goals
- **Thorough**: Reviews catch bugs, design issues, and style problems
- **Respectful**: Feedback is constructive, not personal
- **Efficient**: Reviews complete within 24 hours
- **Educational**: Reviews help developers improve

## Architecture
```
Author → PR → Assign Reviewers → Review → Changes → Re-review → Approve → Merge
                                            │
                                            ▼
                                      Feedback Loop
```

## Components

### Review Checklist

#### Functionality
- Does the code do what it's supposed to?
- Are there edge cases not handled?
- Are error conditions handled properly?
- Does the code work with existing features?

#### Design
- Does the change fit the architecture?
- Are there cleaner/better approaches?
- Does it follow single responsibility?
- Are abstractions appropriate?

#### Security
- Are inputs validated?
- Are there injection vulnerabilities?
- Is sensitive data handled correctly?
- Are permissions checked?

#### Style
- Does it follow coding standards?
- Are naming convention correct?
- Is the code readable?
- Are there unnecessary comments?

#### Testing
- Are there tests for the change?
- Do tests cover edge cases?
- Are tests meaningful?
- Do existing tests still pass?

### Review Process
1. Author creates PR with description
2. CI runs linting, tests, security scan
3. Assign 1-2 reviewers (2 for core changes)
4. Reviewers provide feedback within 24 hours
5. Author addresses feedback
6. Re-review if significant changes
7. Approve and merge (squash)

## Data Flow
PR → CI Checks → Review → Feedback → Changes → Approval → Merge

## Public Interfaces
- PR template: `.github/PULL_REQUEST_TEMPLATE.md`
- Review assignment: automatic based on code owner
- Approval requirement: 1 reviewer (standard), 2 (core changes)

## Configuration
- Required reviewers: code owners defined in `.github/CODEOWNERS`
- Auto-merge: enabled after approval and CI pass
- Branch protection: require PR review, passing checks

## Dependencies
- GitHub (pull request platform)
- CI (test and lint automation)

## Security Considerations
- Security-critical changes must have security team review
- Dependency updates require review
- Secret scanning is part of review

## Failure Recovery
- Review blocked on issues → author proposes alternatives
- Reviewer unavailable → reassign
- Merge conflict → fix in feature branch

## Future Improvements
- Phase 2: Automated review suggestions (AI-assisted)
- Phase 3: Review analytics and metrics

## Engineering Notes
Review code, not the author. Assume good intent. Be specific and constructive.

## Acceptance Criteria
- All PRs require at least one review
- Review checklist is followed
- Core changes require two reviewers
- Review completes within 24 hours
- Feedback is constructive and specific

## References
- Volume-6-Engineering/01-Coding-Standards.md
- Volume-6-Engineering/03-Git-Workflow.md
- Volume-6-Engineering/07-Contributing.md
