# Developer Mode

## Purpose
Define the Developer Mode — the specialized capability set for developers who want to use IRIS as a coding assistant, API client, and development automation tool.

## Responsibilities
- Provide code generation and review capabilities
- Execute and debug code in sandboxed environments
- Generate and run unit tests
- Document code automatically
- Provide API development and testing tools
- Integrate with version control systems

## Design Goals
- **Context-aware**: Understands project structure and conventions
- **Multi-language**: Supports major programming languages
- **Sandboxed**: Code execution in isolated environments
- **Productive**: Automates repetitive development tasks

## Architecture
```
Developer Request → Developer Mode → Language Adapter → Tool Execution → Result
                                              │
                                    ┌─────────┴─────────┐
                                    ▼                   ▼
                              Code Generator      Code Executor
                                    ▼                   ▼
                              Code Reviewer        Test Runner
```

## Components
- **Code Generator**: Generates code from natural language
- **Code Reviewer**: Analyzes code for bugs, style, security
- **Code Executor**: Runs code in sandboxed environment
- **Test Generator**: Auto-generates unit tests
- **Documentation Generator**: Generates docstrings and docs
- **Version Control**: Git integration (commit, branch, PR)
- **API Client**: HTTP request builder and tester

## Data Flow
Request → Language Detection → Generator/Reviewer/Executor → Result → Response

## Public Interfaces
- `POST /dev/generate` → Generate code
- `POST /dev/review` → Review code
- `POST /dev/execute` → Execute code in sandbox
- `POST /dev/test` → Generate and run tests
- `POST /dev/document` → Generate documentation
- `POST /dev/git` → Git operations
- `POST /dev/api` → Build and test API requests

## Configuration
- Developer mode enabled: `dev_mode_enabled` (default: false)
- Sandbox type: `sandbox_type` (default: container)
- Allowed languages: `allowed_languages` (default: all)
- Max execution time: `max_execution_time` (default: 30s)
- Git integration: `git_integration` (default: true)

## Dependencies
- Language-specific compilers/interpreters (for sandbox)
- Git CLI (for version control)
- Container runtime (optional, for sandboxing)
- Inference Engine (code generation)

## Security Considerations
- Code execution is sandboxed (container or subprocess with restrictions)
- Network access from sandbox is blocked by default
- File system access is restricted to sandbox directory
- Git operations require user confirmation
- Generated code is reviewed and not trusted automatically

## Failure Recovery
- Code execution timeout → kill process → return partial output
- Syntax error → return error with line number
- Sandbox failure → fallback to syntax-only analysis
- Git operation failure → clear error with manual steps

## Future Improvements
- Phase 2: Multi-file refactoring
- Phase 3: Full IDE integration
- Phase 4: Automated PR review

## Engineering Notes
Developer mode is the most feature-dense capability. Prioritize stability and accuracy over feature count.

## Acceptance Criteria
- Code generation produces syntactically correct code
- Code review identifies common bugs and security issues
- Code execution runs in sandbox without system access
- Test generation produces valid test cases
- Git operations work with standard Git workflows

## References
- Volume-3-Capabilities/07-Terminal-Control.md
- Volume-6-Engineering/01-Coding-Standards.md
- Volume-6-Engineering/05-Testing.md
