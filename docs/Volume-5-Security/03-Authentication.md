# Authentication

## Purpose
Define the Authentication system — the mechanisms for verifying user identity, managing sessions, and securing API access.

## Responsibilities
- Verify user identity during login
- Issue and validate JWT tokens
- Manage user sessions
- Handle password hashing and validation
- Support API token authentication for programmatic access
- Provide single sign-on integration (future)

## Design Goals
- **Secure**: Industry-standard hashing and token algorithms
- **Stateless**: JWT-based, no server-side session storage
- **Fast**: Authentication completes in < 100ms
- **Extensible**: Support multiple auth methods

## Architecture
```
Login → Credential Validation → JWT Issuance → Token → API Access
                                                     │
                                                     ▼
                                              Token Validation (middleware)
```

## Components
- **Credential Validator**: Validates username/password against hashed store
- **JWT Manager**: Issues and validates JWT tokens
- **Password Hasher**: Hashes and verifies passwords (bcrypt)
- **Token Middleware**: FastAPI middleware for token validation
- **API Token Manager**: Issues and revokes API tokens

## Data Flow
Login Request → Credential Validator → Password Hasher → JWT Manager → Token Response

Request → Token Middleware → JWT Validation → Authenticated Context

## Public Interfaces
- `POST /auth/signup` → Create account
- `POST /auth/login` → Authenticate and receive token
- `GET /auth/me` → Get current user info
- `POST /auth/refresh` → Refresh JWT token
- `POST /auth/change-password` → Change password
- `POST /auth/api-token` → Generate API token

## Configuration
- JWT secret: `JWT_SECRET` (environment variable)
- Token expiry: `auth_token_expiry_minutes` (default: 60)
- Refresh token expiry: `refresh_token_expiry_days` (default: 7)
- Password hash algorithm: `bcrypt` (default)
- Max login attempts: `max_login_attempts` (default: 5)
- Account lockout duration: `lockout_minutes` (default: 30)

## Dependencies
- PyJWT (JWT handling)
- bcrypt (password hashing)
- PostgreSQL (user store)
- FastAPI middleware

## Security Considerations
- Passwords hashed with bcrypt (cost factor 12+)
- JWT tokens signed with HS256 or RS256
- Tokens expire after configured duration
- Refresh tokens have separate, longer expiry
- Failed login attempts are rate-limited
- Account lockout after max attempts
- Token secrets stored in environment variables, never in code

## Failure Recovery
- Token validation failure → return 401 with clear message
- Password hash mismatch → generic "invalid credentials" error
- Account locked → return lockout remaining time
- JWT secret missing → crash on startup (safe failure)

## Future Improvements
- Phase 2: OAuth2 social login
- Phase 3: WebAuthn / FIDO2 support
- Phase 4: Biometric authentication

## Engineering Notes
Authentication is the first line of defense. Every endpoint must be protected.

## Acceptance Criteria
- Signup creates user with hashed password
- Login returns valid JWT token
- Token is validated on each request
- Expired tokens are rejected
- Failed login attempts trigger lockout
- Passwords can be changed

## References
- Volume-5-Security/01-Security.md
- Volume-5-Security/04-Permissions.md
- api/routers/auth.py
